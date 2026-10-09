import hashlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from apps.consents.models import ConfirmationMessage, ConsentEvidence, Subscription
from apps.contacts.imports import (
    MAX_BYTES,
    MAX_ROWS,
    apply_import,
    create_import_preview,
    discard_expired_previews,
    parse_export,
)
from apps.contacts.models import Contact, ImportBatch, MailchimpRecord, Suppression
from apps.contacts.services import stage_mailchimp_contact
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

pytestmark = pytest.mark.django_db
DATA = b"Emailadresse,Vorname,Name,Erlaubnis zum Marketing\none@example.com,Max,Example,X\n"


@pytest.fixture
def operator(django_user_model):
    return django_user_model.objects.create_user(username="importer", is_staff=True)


def upload(data=DATA):
    return SimpleUploadedFile("synthetic.csv", data, content_type="text/csv")


def preview(operator, data=DATA):
    return create_import_preview(upload(data), ",", operator, active_export=True)


def test_full_upload_preview_confirm_and_repeat(client, operator):
    client.force_login(operator)
    response = client.post(
        reverse("contact_import_upload"),
        {
            "file": upload(DATA + b"one@example.com,Max,Example,X\n"),
            "delimiter": ",",
            "active_export": "on",
        },
    )
    assert response.status_code == 302
    batch = ImportBatch.objects.get()
    assert not Contact.objects.exists()
    response = client.get(response.url)
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    assert b"one@example.com" in response.content
    assert b"Duplikatzeile" in response.content
    assert response.context["rows"][0]["marketing_flag"] is True
    url = reverse("contact_import_preview", args=[batch.id])
    # Checkbox missing: no contact writes.
    assert client.post(url, {}).status_code == 200
    assert not Contact.objects.exists()
    response = client.post(url, {"confirm": "on", "rows": "tampered client data"})
    assert response.status_code == 302
    batch.refresh_from_db()
    assert batch.result == {"new": 1, "existing": 0, "duplicates": 1, "blocked": 0}
    assert batch.status == "completed"
    assert batch.rows == []
    assert Contact.objects.get().email == "one@example.com"
    assert Subscription.objects.get().status == "imported"
    assert not ConfirmationMessage.objects.exists()
    assert not ConsentEvidence.objects.exists()
    assert client.post(url, {"confirm": "on"}).status_code == 302
    assert MailchimpRecord.objects.count() == 1
    assert b"abgeschlossen" in client.get(url).content


def test_authorization_and_owner_isolation(client, operator, django_user_model):
    batch = preview(operator)
    url = reverse("contact_import_preview", args=[batch.id])
    assert client.get(url).status_code == 302
    other = django_user_model.objects.create_user(username="other", is_staff=True)
    client.force_login(other)
    assert client.get(url).status_code == 404
    assert client.post(url, {"confirm": "on"}).status_code == 404
    other.is_staff = False
    other.save()
    assert client.get(reverse("contact_import_upload")).status_code == 403
    with pytest.raises(PermissionDenied):
        apply_import(batch.id, other)
    assert not Contact.objects.exists()


def test_csrf_upload_and_confirmation(operator):
    client = Client(enforce_csrf_checks=True)
    client.force_login(operator)
    url = reverse("contact_import_upload")
    assert (
        client.post(url, {"file": upload(), "delimiter": ",", "active_export": "on"}).status_code
        == 403
    )
    client.get(url)
    token = client.cookies["csrftoken"].value
    response = client.post(
        url,
        {"file": upload(), "delimiter": ",", "active_export": "on", "csrfmiddlewaretoken": token},
        HTTP_ORIGIN="http://testserver",
    )
    assert response.status_code == 302
    url = response.url
    assert client.post(url, {"confirm": "on"}).status_code == 403
    assert (
        client.post(
            url,
            {"confirm": "on", "csrfmiddlewaretoken": token},
            HTTP_ORIGIN="https://foreign.example",
        ).status_code
        == 403
    )
    assert (
        client.post(
            url, {"confirm": "on", "csrfmiddlewaretoken": token}, HTTP_ORIGIN="http://testserver"
        ).status_code
        == 302
    )


def test_invalid_and_conflicting_rows_block_all_writes(operator):
    for data in (DATA + b"invalid,Other,Example,\n", DATA + b"one@example.com,Other,Example,X\n"):
        batch = preview(operator, data)
        assert any(entry["errors"] for entry in batch.rows)
        with pytest.raises(ValidationError):
            apply_import(batch.id, operator)
    assert not Contact.objects.exists()


def test_status_changed_after_preview_is_preserved(operator, client):
    batch = preview(operator)
    contact = Contact.objects.create(
        email="one@example.com", email_key="one@example.com", first_name="Local name"
    )
    Subscription.objects.create(contact=contact, status="unsubscribed")
    Suppression.objects.create(contact=contact, reason="manual")
    client.force_login(operator)
    response = client.get(reverse("contact_import_preview", args=[batch.id]))
    assert b"Gesperrt" in response.content
    result = apply_import(batch.id, operator)
    contact.refresh_from_db()
    assert contact.first_name == "Local name"
    assert contact.subscription.status == "unsubscribed"
    assert result.result["existing"] == 1
    assert result.result["blocked"] == 1


def test_failure_rolls_back_entire_import(operator):
    batch = preview(operator, DATA + b"two@example.com,Other,Example,\n")

    def fail_second(row, batch_id):
        if row["Emailadresse"] == "two@example.com":
            raise ValidationError("Synthetic failure")
        return stage_mailchimp_contact(row, batch_id)

    with patch("apps.contacts.imports.stage_mailchimp_contact", side_effect=fail_second):
        with pytest.raises(ValidationError):
            apply_import(batch.id, operator)
    assert not Contact.objects.exists()
    assert not MailchimpRecord.objects.exists()
    batch.refresh_from_db()
    assert batch.status == "preview"
    assert len(batch.rows) == 2


def test_expiry_and_cancel_clear_personal_preview_data(client, operator):
    client.force_login(operator)
    batch = preview(operator)
    ImportBatch.objects.filter(pk=batch.id).update(expires_at=timezone.now() - timedelta(seconds=1))
    url = reverse("contact_import_preview", args=[batch.id])
    assert b"one@example.com" not in client.get(url).content
    with pytest.raises(ValidationError):
        apply_import(batch.id, operator)
    assert discard_expired_previews() == 1
    batch.refresh_from_db()
    assert batch.rows == []
    batch = preview(operator)
    url = reverse("contact_import_preview", args=[batch.id])
    assert client.post(url, {"action": "cancel"}).status_code == 302
    batch.refresh_from_db()
    assert batch.status == "cancelled" and batch.rows == []
    assert not Contact.objects.exists()


@pytest.mark.parametrize("delimiter", [",", ";", "\t"])
def test_delimiters_bom_and_quoted_values(delimiter):
    text = (
        f"Email Address{delimiter}Vorname{delimiter}Name\r\n"
        f'one@example.com{delimiter}"Max{delimiter}Other"{delimiter}Example\r\n'
    )
    rows, ignored = parse_export(b"\xef\xbb\xbf" + text.encode(), delimiter)
    assert rows[0]["row"]["Vorname"] == f"Max{delimiter}Other"
    assert ignored == []


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"Emailadresse\n",
        b"Name\nMax\n",
        b"Emailadresse,Emailadresse\na@b.com,a@b.com\n",
        b"Emailadresse\n\xff\n",
        b"Emailadresse\n\x00\n",
        b'Emailadresse\n"unterminated\n',
    ],
)
def test_malformed_files_rejected(data):
    with pytest.raises(ValidationError):
        parse_export(data, ",")


def test_limits_unknown_columns_and_checksum(operator):
    with pytest.raises(ValidationError):
        parse_export(b"x" * (MAX_BYTES + 1), ",")
    with pytest.raises(ValidationError):
        parse_export(b"Emailadresse\n" + b"one@example.com\n" * (MAX_ROWS + 1), ",")
    batch = preview(operator, b"Emailadresse,Unknown\none@example.com,not retained\n")
    assert batch.ignored_columns == ["Unknown"]
    assert "Unknown" not in batch.rows[0]["row"]
    assert (
        batch.file_sha256
        == hashlib.sha256(b"Emailadresse,Unknown\none@example.com,not retained\n").hexdigest()
    )
    assert batch.filename == "synthetic.csv"
    assert batch.owner == operator


def test_active_export_confirmation_is_required(operator):
    with pytest.raises(ValidationError):
        create_import_preview(upload(), ",", operator, active_export=False)
    assert not ImportBatch.objects.exists()


def test_second_upload_and_case_duplicate_do_not_duplicate_contacts(operator):
    batch = preview(operator, DATA + b"ONE@example.com,Max,Example,X\n")
    assert batch.rows[1]["duplicate"]
    assert apply_import(batch.id, operator).result["new"] == 1
    second = preview(operator)
    assert apply_import(second.id, operator).result["existing"] == 1
    assert Contact.objects.count() == 1
    assert MailchimpRecord.objects.count() == 2  # Separate source snapshots for separate uploads.


def test_cleanup_command_only_discards_expired_previews(operator):
    first = preview(operator)
    second = preview(operator)
    completed = preview(operator)
    apply_import(completed.id, operator)
    ImportBatch.objects.filter(pk=first.id).update(expires_at=timezone.now() - timedelta(minutes=1))
    call_command("discard_import_previews")
    first.refresh_from_db()
    second.refresh_from_db()
    completed.refresh_from_db()
    assert first.status == "cancelled" and first.rows == []
    assert second.status == "preview" and second.rows
    assert completed.status == "completed" and completed.result


def test_html_in_source_is_escaped_in_preview(client, operator):
    client.force_login(operator)
    batch = preview(operator, DATA.replace(b"Max", b"<script>alert(1)</script>"))
    response = client.get(reverse("contact_import_preview", args=[batch.id]))
    assert b"<script>" not in response.content
    assert b"&lt;script&gt;" in response.content
