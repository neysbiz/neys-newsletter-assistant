import uuid

import pytest
from apps.consents.models import ConfirmationMessage, ConsentEvidence, Subscription
from apps.consents.policies import can_send_campaign
from apps.consents.services import confirm_subscription, request_subscription, unsubscribe
from apps.consents.tokens import encode_reference
from apps.contacts.models import Contact, MailchimpRecord, Suppression
from apps.contacts.services import prepare_mailchimp_row, stage_mailchimp_contact
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


@pytest.fixture
def row():
    return {
        "Emailadresse": " Test@example.com ",
        "Vorname": "Max",
        "Name": "Beispiel",
        "Status": "aktiv",
        "Erlaubnis zum Marketing": "X",
        "OPTIN_TIME": "2020-09-18 14:30:28",
        "CONFIRM_TIME": "2020-09-18 14:30:28",
        "TIMEZONE": "europe/berlin",
        "LEID": "12345",
        "EUID": "synthetic-id",
        "SOURCE": "List Import from Dateiupload",
    }


def test_import_is_staged_without_consent_or_mail(row):
    contact, record, created = stage_mailchimp_contact(row, uuid.uuid4())
    assert created
    assert contact.email_key == "test@example.com"
    assert contact.first_name == "Max"
    assert contact.last_name == "Beispiel"
    assert record.source_status == "subscribed"
    assert record.marketing_flag is True
    assert record.source_data["OPTIN_TIME"] == row["OPTIN_TIME"]
    assert contact.subscription.status == "imported"
    assert not contact.subscription.tracking_allowed
    assert not can_send_campaign(contact.id)
    assert not ConfirmationMessage.objects.exists()
    assert not ConsentEvidence.objects.exists()


def test_repeat_import_preserves_local_withdrawal_and_suppression(row):
    batch = uuid.uuid4()
    contact, record, _ = stage_mailchimp_contact(row, batch)
    assert not stage_mailchimp_contact(row, batch)[2]
    request_subscription(contact.email, "192.0.2.1")
    token = contact.subscription.confirmationtoken_set.get()
    assert confirm_subscription(encode_reference(token.id, "confirmation"))
    assert unsubscribe(encode_reference(contact.subscription.id, "unsubscribe"))
    Suppression.objects.create(contact=contact, reason="manual")
    stage_mailchimp_contact(row, uuid.uuid4())
    assert Subscription.objects.get(contact=contact).status == "unsubscribed"
    assert Suppression.objects.filter(contact=contact).exists()
    assert not can_send_campaign(contact.id)
    assert MailchimpRecord.objects.count() == 2
    assert record.pk == MailchimpRecord.objects.get(batch_id=batch).pk


def test_duplicate_conflict_fails_without_overwriting(row):
    batch = uuid.uuid4()
    stage_mailchimp_contact(row, batch)
    with pytest.raises(ValidationError):
        stage_mailchimp_contact({**row, "Vorname": "Other"}, batch)
    assert Contact.objects.get().first_name == "Max"
    assert MailchimpRecord.objects.count() == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("Status", "unsubscribed"),
        ("Status", "cleaned"),
        ("Emailadresse", "invalid"),
        ("Erlaubnis zum Marketing", "perhaps"),
        ("Name", "x" * 151),
    ],
)
def test_invalid_source_rows_cannot_write(row, field, value):
    with pytest.raises(ValidationError):
        stage_mailchimp_contact({**row, field: value}, uuid.uuid4())
    assert not Contact.objects.exists()


def test_missing_and_conflicting_email_rejected(row):
    with pytest.raises(ValidationError):
        prepare_mailchimp_row({key: value for key, value in row.items() if key != "Emailadresse"})
    with pytest.raises(ValidationError):
        prepare_mailchimp_row({**row, "Email Address": "other@example.com"})


def test_active_export_default_and_absent_flag_are_explicit(row):
    prepared = prepare_mailchimp_row(
        {
            key: value
            for key, value in row.items()
            if key not in ("Status", "Erlaubnis zum Marketing")
        }
    )
    assert prepared["source_status"] == "subscribed"
    assert prepared["marketing_flag"] is None
