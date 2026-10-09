from datetime import timedelta
from unittest.mock import patch

import pytest
from apps.consents.delivery import dispatch_confirmations
from apps.consents.models import (
    ConfirmationMessage,
    ConfirmationToken,
    ConsentEvent,
    ConsentEvidence,
    RateLimitBucket,
    Subscription,
)
from apps.consents.policies import can_send_campaign
from apps.consents.services import confirm_subscription, request_subscription, unsubscribe
from apps.consents.tokens import encode_reference
from apps.contacts.models import Contact, Suppression
from django.core import mail
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

pytestmark = pytest.mark.django_db


@pytest.fixture
def pending():
    request_subscription("Partner@example.com", "127.0.0.1")
    return Subscription.objects.get()


def confirmation(subscription):
    token = ConfirmationToken.objects.get(subscription=subscription)
    return encode_reference(token.id, "confirmation")


def withdrawal(subscription):
    return encode_reference(subscription.id, "unsubscribe")


def test_full_workflow_and_fresh_send_policy(pending):
    assert not can_send_campaign(pending.contact_id)
    assert confirm_subscription(confirmation(pending))
    assert can_send_campaign(pending.contact_id)
    pending.refresh_from_db()
    assert not pending.tracking_allowed
    assert unsubscribe(withdrawal(pending))
    assert not can_send_campaign(pending.contact_id)
    assert list(ConsentEvent.objects.values_list("name", flat=True)) == [
        "subscription.confirmed",
        "subscription.withdrawn",
    ]


def test_confirmation_get_cannot_activate_and_post_needs_csrf(pending):
    client = Client(enforce_csrf_checks=True)
    url = reverse("confirm", args=[confirmation(pending)])
    assert client.get(url).status_code == 200
    pending.refresh_from_db()
    assert pending.status == "pending"
    assert client.post(url).status_code == 403
    token = client.cookies["csrftoken"].value
    assert client.post(url, {"csrfmiddlewaretoken": token}).status_code == 200
    assert can_send_campaign(pending.contact_id)


def test_unsubscribe_get_is_safe_and_browser_post_needs_csrf(pending):
    confirm_subscription(confirmation(pending))
    client = Client(enforce_csrf_checks=True)
    url = reverse("unsubscribe", args=[withdrawal(pending)])
    assert client.get(url).status_code == 200
    assert can_send_campaign(pending.contact_id)
    assert client.post(url).status_code == 403
    assert (
        client.post(url, {"csrfmiddlewaretoken": client.cookies["csrftoken"].value}).status_code
        == 200
    )
    assert not can_send_campaign(pending.contact_id)


@pytest.mark.parametrize("value", ["bad", "", "4bd4bb28-3c22-4548-820d-5a1e3df6d500:bad"])
def test_invalid_tokens_never_mutate(pending, value):
    assert not confirm_subscription(value)
    assert not unsubscribe(value)
    pending.refresh_from_db()
    assert pending.status == "pending"


def test_purpose_bound_token(pending):
    assert not unsubscribe(confirmation(pending))
    assert not confirm_subscription(withdrawal(pending))


def test_expired_token_cannot_activate(pending):
    ConfirmationToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert not confirm_subscription(confirmation(pending))
    assert not can_send_campaign(pending.contact_id)


def test_repeated_operations_are_idempotent_and_old_confirm_does_not_reactivate(pending):
    token = confirmation(pending)
    assert confirm_subscription(token)
    assert confirm_subscription(token)
    assert ConsentEvidence.objects.filter(action="confirmed").count() == 1
    assert unsubscribe(withdrawal(pending))
    assert unsubscribe(withdrawal(pending))
    assert ConsentEvidence.objects.filter(action="withdrawn").count() == 1
    assert not confirm_subscription(token)


def test_suppression_blocks_confirmation_and_dispatch_permission(pending):
    Suppression.objects.create(contact_id=pending.contact_id, reason="complaint")
    assert not confirm_subscription(confirmation(pending))
    assert not can_send_campaign(pending.contact_id)


def test_confirmation_evidence_preserves_original_version(pending):
    original = ConsentEvidence.objects.get(action="requested")
    with override_settings(NEWSLETTER_CONSENT_VERSION="changed", NEWSLETTER_CONSENT_TEXT="Changed"):
        assert confirm_subscription(confirmation(pending))
    accepted = ConsentEvidence.objects.get(action="confirmed")
    assert accepted.text == original.text
    assert accepted.text_version == original.text_version


def test_duplicate_request_cooldown_and_case_normalization(pending):
    request_subscription("partner@EXAMPLE.COM", "127.0.0.1")
    assert Contact.objects.count() == 1
    assert ConfirmationMessage.objects.count() == 1


def test_provider_specific_email_parts_are_preserved():
    request_subscription("a.b+tag@example.com", "127.0.0.1")
    assert Contact.objects.get().email_key == "a.b+tag@example.com"


def test_new_request_invalidates_expired_or_older_links(pending):
    old = confirmation(pending)
    ConfirmationToken.objects.update(expires_at=timezone.now() + timedelta(hours=23))
    request_subscription("partner@example.com", "127.0.0.1")
    assert ConfirmationToken.objects.count() == 2
    assert not confirm_subscription(old)
    assert ConfirmationMessage.objects.filter(status="cancelled").count() == 1


def test_ip_rate_limit_and_no_raw_ip_storage():
    for i in range(25):
        request_subscription(f"user{i}@example.com", "192.0.2.100")
    assert Contact.objects.count() == 20
    assert all(
        "192.0.2.100" not in key for key in RateLimitBucket.objects.values_list("key", flat=True)
    )


def test_public_response_does_not_reveal_active_or_blocked_subscription(client, pending):
    url = reverse("subscribe")
    first = client.post(url, {"email": "new@example.com", "consent": "on"})
    confirm_subscription(confirmation(pending))
    second = client.post(url, {"email": "Partner@example.com", "consent": "on"})
    assert first.content == second.content


def test_checkbox_is_required(client):
    assert client.post(reverse("subscribe"), {"email": "new@example.com"}).status_code == 200
    assert Contact.objects.count() == 0


def test_durable_confirmation_sends_once_and_contains_no_tracking(pending):
    assert len(mail.outbox) == 0
    dispatch_confirmations()
    dispatch_confirmations()
    assert len(mail.outbox) == 1
    assert "/confirm/" in mail.outbox[0].body
    assert "<img" not in mail.outbox[0].body
    assert ConfirmationMessage.objects.get().status == "accepted"


def test_timeout_is_uncertain_and_not_automatically_retried(pending):
    with patch("apps.consents.delivery.EmailMultiAlternatives.send", side_effect=TimeoutError):
        dispatch_confirmations()
    assert ConfirmationMessage.objects.get().status == "uncertain"
    dispatch_confirmations()
    assert len(mail.outbox) == 0


def test_crashed_claim_is_marked_uncertain(pending):
    ConfirmationMessage.objects.update(
        status="sending", updated_at=timezone.now() - timedelta(minutes=11)
    )
    dispatch_confirmations()
    assert ConfirmationMessage.objects.get().status == "uncertain"
    assert len(mail.outbox) == 0


def test_unsubscribe_cancels_pending_doi(pending):
    unsubscribe(withdrawal(pending))
    dispatch_confirmations()
    assert len(mail.outbox) == 0
    assert not confirm_subscription(confirmation(pending))


def test_rfc8058_endpoint_validates_body_and_does_not_redirect(pending):
    confirm_subscription(confirmation(pending))
    client = Client(enforce_csrf_checks=True)
    url = reverse("one_click_unsubscribe", args=[withdrawal(pending)])
    assert client.get(url).status_code == 405
    assert client.post(url, {}).status_code == 400
    assert can_send_campaign(pending.contact_id)
    response = client.post(url, {"List-Unsubscribe": "One-Click"})
    assert response.status_code == 200
    assert "Location" not in response
    assert not can_send_campaign(pending.contact_id)


def test_contact_list_is_staff_only(client, django_user_model):
    user = django_user_model.objects.create_user(username="regular")
    client.force_login(user)
    assert client.get(reverse("contacts")).status_code == 403
    user.is_staff = True
    user.save()
    assert client.get(reverse("contacts")).status_code == 200


@pytest.mark.parametrize("page", ["subscribe", "confirm", "unsubscribe"])
def test_public_forms_preserve_origin_without_external_referrers(client, pending, page):
    reference = confirmation(pending) if page == "confirm" else withdrawal(pending)
    url = reverse(page) if page == "subscribe" else reverse(page, args=[reference])
    response = client.get(url)
    assert response["Cache-Control"] == "no-store"
    assert response["Referrer-Policy"] == "same-origin"


def test_suppression_added_after_request_cancels_doi(pending):
    Suppression.objects.create(contact_id=pending.contact_id, reason="hard_bounce")
    dispatch_confirmations()
    assert not mail.outbox
    assert ConfirmationMessage.objects.get().status == "cancelled"


@pytest.mark.parametrize("secure", [False, True])
def test_confirmation_post_validates_browser_origin(pending, secure):
    client = Client(enforce_csrf_checks=True)
    url = reverse("confirm", args=[confirmation(pending)])
    client.get(url, secure=secure)
    data = {"csrfmiddlewaretoken": client.cookies["csrftoken"].value}
    for origin in ["null", "https://foreign.example"]:
        assert client.post(url, data, secure=secure, HTTP_ORIGIN=origin).status_code == 403
    assert not can_send_campaign(pending.contact_id)
    origin = "https://testserver" if secure else "http://testserver"
    assert client.post(url, data, secure=secure, HTTP_ORIGIN=origin).status_code == 200
    assert can_send_campaign(pending.contact_id)
