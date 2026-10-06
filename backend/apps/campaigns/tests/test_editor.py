from io import BytesIO

import pytest
from apps.campaigns.models import Campaign, RevisionAsset
from apps.campaigns.rendering import render_revision
from apps.campaigns.services import freeze_revision, save_draft, upload_asset
from apps.campaigns.testing import send_test_mail
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.deletion import ProtectedError
from django.test import override_settings
from django.urls import reverse
from PIL import Image

pytestmark = pytest.mark.django_db


@pytest.fixture
def revision():
    campaign = save_draft(
        "Hallo {{email}}",
        "Neue Mode",
        [
            {"type": "text", "text": "<script>alert(1)</script>\nHallo {{email}}"},
            {"type": "link", "label": "Mehr entdecken", "url": "https://example.com/fashion"},
        ],
    )
    return freeze_revision(campaign.id)


@pytest.fixture
def operator(client, django_user_model):
    user = django_user_model.objects.create_user(username="editor", is_staff=True)
    client.force_login(user)
    return client


def test_revision_stays_frozen_after_draft_edit(revision):
    save_draft(
        "Geändert",
        "",
        [{"type": "text", "text": "Anderer Inhalt"}],
        campaign_id=revision.campaign_id,
    )
    revision.refresh_from_db()
    assert revision.subject == "Hallo {{email}}"
    assert revision.blocks[0]["text"].startswith("<script>")
    with pytest.raises(ValidationError):
        revision.save()


def test_html_escapes_content_but_text_remains_readable(revision):
    result = render_revision(
        revision, email="partner@example.com", unsubscribe_url="https://example.com/bye"
    )
    assert "<script>" not in result.html
    assert "&lt;script&gt;" in result.html
    assert "Hallo partner@example.com" in result.text
    assert "Mehr entdecken: https://example.com/fashion" in result.text
    assert "Newsletter abmelden: https://example.com/bye" in result.text
    assert result.subject == "Hallo partner@example.com"
    assert "tracking" not in result.html


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "javascript:alert(1)",
        "https://user:pass@example.com",
        "data:text/html,evil",
    ],
)
def test_dangerous_links_are_rejected(url):
    with pytest.raises(ValidationError):
        save_draft("Betreff", "", [{"type": "link", "label": "Klick", "url": url}])
    assert not Campaign.objects.exists()


@pytest.mark.parametrize("text", ["{{name}}", "{{email", "email}}"])
def test_unknown_or_broken_placeholders_are_rejected(text):
    with pytest.raises(ValidationError):
        save_draft("Betreff", "", [{"type": "text", "text": text}])


def test_subject_header_injection_is_rejected():
    with pytest.raises(ValidationError):
        save_draft("Betreff\nBcc: attacker@example.com", "", [{"type": "text", "text": "Hello"}])


def test_decoded_image_is_reencoded_and_frozen_image_is_protected(tmp_path):
    source = BytesIO()
    Image.new("RGB", (80, 40), "red").save(source, "PNG")
    with override_settings(MEDIA_ROOT=tmp_path, PUBLIC_BASE_URL="https://example.com"):
        asset = upload_asset(
            "Kollektion",
            SimpleUploadedFile("input.exe", source.getvalue(), content_type="image/png"),
        )
        assert asset.file.name.endswith(".jpg")
        assert "input.exe" not in asset.file.name
        revision = freeze_revision(
            save_draft(
                "Bilder", "", [{"type": "image", "asset_id": str(asset.id), "alt": "Rotes Kleid"}]
            ).id
        )
        assert RevisionAsset.objects.filter(revision=revision, asset=asset).exists()
        result = render_revision(
            revision, email="test@example.com", unsubscribe_url="https://example.com/bye"
        )
        assert "https://example.com/media-images/" in result.html
        assert 'alt="Rotes Kleid"' in result.html
        with pytest.raises(ProtectedError):
            asset.delete()


def test_fake_image_is_rejected(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path), pytest.raises(ValidationError):
        upload_asset(
            "Bild",
            SimpleUploadedFile("fake.jpg", b"<script>evil</script>", content_type="image/jpeg"),
        )


def test_image_requires_alt_text(tmp_path):
    with pytest.raises(ValidationError):
        save_draft("Bilder", "", [{"type": "image", "asset_id": "invalid", "alt": ""}])


def test_testmail_uses_same_rendered_revision(revision):
    send_test_mail(revision, "test@example.com")
    expected = render_revision(
        revision,
        email="test@example.com",
        unsubscribe_url="http://localhost:8005/test-unsubscribe/",
    )
    assert mail.outbox[0].subject == expected.subject
    assert mail.outbox[0].body == expected.text
    assert mail.outbox[0].alternatives[0].content == expected.html


def test_editor_can_save_with_unused_extra_block(operator):
    response = operator.post(
        reverse("campaign_new"),
        {
            "subject": "Neue Kollektion",
            "preheader": "Entdecken",
            "blocks-TOTAL_FORMS": "2",
            "blocks-INITIAL_FORMS": "0",
            "blocks-MIN_NUM_FORMS": "0",
            "blocks-MAX_NUM_FORMS": "20",
            "blocks-0-type": "text",
            "blocks-0-text": "Willkommen",
            "blocks-0-ORDER": "1",
            "blocks-1-type": "",
            "blocks-1-text": "",
        },
    )
    assert response.status_code == 302
    assert Campaign.objects.get().blocks == [{"type": "text", "text": "Willkommen"}]


def test_public_cannot_access_editor_or_testmail(client, revision):
    assert client.get(reverse("campaign_new")).status_code == 302
    assert (
        client.post(
            reverse("revision_test", args=[revision.id]), {"recipient": "test@example.com"}
        ).status_code
        == 302
    )
    assert not mail.outbox


def test_preview_is_protected_and_has_content_policy(operator, revision):
    response = operator.get(reverse("revision_preview", args=[revision.id]))
    assert response.status_code == 200
    assert "default-src 'none'" in response["Content-Security-Policy"]
    assert response["Cache-Control"] == "no-store"


def test_revision_numbers_are_monotonic(revision):
    second = freeze_revision(revision.campaign_id)
    assert second.number == revision.number + 1
