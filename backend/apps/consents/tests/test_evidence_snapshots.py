import hashlib

import pytest
from apps.consents.delivery import dispatch_confirmations
from apps.consents.models import ConfirmationMessage, ConfirmationToken, ConsentEvidence
from apps.consents.services import confirm_subscription, request_subscription, unsubscribe
from apps.consents.tokens import encode_reference
from django.core import mail
from django.test import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_doi_preserves_displayed_text_privacy_and_mail_snapshot(client):
    with override_settings(
        NEWSLETTER_CONSENT_VERSION="v1",
        NEWSLETTER_CONSENT_TEXT="Original newsletter purpose",
        NEWSLETTER_PRIVACY_VERSION="p1",
        NEWSLETTER_PRIVACY_TEXT="Original privacy notice",
        DEFAULT_FROM_EMAIL="original@example.com",
    ):
        response = client.get(reverse("subscribe"))
        assert b"Original privacy notice" in response.content
        request_subscription("snapshot@example.com", "192.0.2.1")
    token = ConfirmationToken.objects.get()
    link = encode_reference(token.id, "confirmation")
    requested = token.evidence
    assert requested.email_snapshot == "snapshot@example.com"
    assert requested.remote_address is None
    assert requested.text_sha256 == hashlib.sha256(requested.text.encode()).hexdigest()
    with override_settings(
        NEWSLETTER_CONSENT_TEXT="Changed purpose",
        NEWSLETTER_PRIVACY_TEXT="Changed privacy notice",
        DEFAULT_FROM_EMAIL="changed@example.com",
    ):
        response = client.get(reverse("confirm", args=[link]))
        assert b"Original newsletter purpose" in response.content
        assert b"Original privacy notice" in response.content
        assert b"Changed purpose" not in response.content
        dispatch_confirmations()
        assert confirm_subscription(link)
        assert confirm_subscription(link)
    confirmed = ConsentEvidence.objects.get(action="confirmed")
    assert confirmed.request_evidence_id == requested.id
    assert confirmed.confirmation_reference == token.id
    assert confirmed.privacy_version == "p1"
    assert confirmed.privacy_text == requested.privacy_text
    assert confirmed.text_sha256 == requested.text_sha256
    assert confirmed.email_snapshot == requested.email_snapshot
    message = ConfirmationMessage.objects.get()
    assert message.accepted_at >= message.attempted_at
    assert message.recipient == "snapshot@example.com"
    assert mail.outbox[0].from_email == "original@example.com"
    assert message.body_sha256 == hashlib.sha256(mail.outbox[0].body.encode()).hexdigest()
    assert "{{confirmation_link}}" in message.body_snapshot
    assert link not in message.body_snapshot
    assert str(message.message_id) in mail.outbox[0].extra_headers["Message-ID"]
    assert unsubscribe(encode_reference(token.subscription_id, "unsubscribe"))
    withdrawn = ConsentEvidence.objects.get(action="withdrawn")
    assert withdrawn.request_evidence_id == requested.id
    assert withdrawn.privacy_text == requested.privacy_text


@override_settings(NEWSLETTER_STORE_EVIDENCE_IP=True)
def test_optional_ip_evidence_uses_request_peer(client):
    request_subscription("ip@example.com", "192.0.2.10")
    token = ConfirmationToken.objects.get()
    assert token.evidence.remote_address == "192.0.2.10"
    link = encode_reference(token.id, "confirmation")
    url = reverse("confirm", args=[link])
    response = client.post(url, REMOTE_ADDR="192.0.2.11", HTTP_X_FORWARDED_FOR="192.0.2.99")
    assert response.status_code == 200
    assert ConsentEvidence.objects.get(action="confirmed").remote_address == "192.0.2.11"


@override_settings(NEWSLETTER_STORE_EVIDENCE_IP=True)
def test_unknown_peer_is_not_fabricated():
    request_subscription("unknown@example.com", "unknown")
    assert ConsentEvidence.objects.get().remote_address is None
