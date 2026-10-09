import hashlib
import ipaddress
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import salted_hmac

from apps.contacts.models import Contact, Suppression
from apps.contacts.services import normalize_email

from .models import (
    ConfirmationMessage,
    ConfirmationToken,
    ConsentEvent,
    ConsentEvidence,
    RateLimitBucket,
    Subscription,
)
from .tokens import decode_reference


def evidence_address(value):
    if not settings.NEWSLETTER_STORE_EVIDENCE_IP:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except (ValueError, TypeError):
        return None


def consume_limits(email_key, remote_address):
    now = timezone.now()
    window = int(now.timestamp()) // 3600
    for kind, value, maximum in [("email", email_key, 3), ("ip", remote_address, 20)]:
        key = salted_hmac("newsletter.rate.v1", f"{kind}:{value}:{window}").hexdigest()
        bucket, _ = RateLimitBucket.objects.get_or_create(
            key=key,
            defaults={"expires_at": now + timedelta(hours=2)},
        )
        bucket = RateLimitBucket.objects.select_for_update().get(pk=bucket.pk)
        if bucket.count >= maximum:
            return False
        bucket.count += 1
        bucket.save(update_fields=["count"])
    return True


@transaction.atomic
def request_subscription(email, remote_address):
    email, email_key = normalize_email(email)
    if not consume_limits(email_key, remote_address):
        return
    contact, _ = Contact.objects.get_or_create(email_key=email_key, defaults={"email": email})
    contact = Contact.objects.select_for_update().get(pk=contact.pk)
    subscription, _ = Subscription.objects.get_or_create(contact=contact)
    subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
    if (
        subscription.status == Subscription.Status.ACTIVE
        or Suppression.objects.filter(
            contact=contact,
        ).exists()
    ):
        return
    now = timezone.now()
    latest = (
        ConfirmationToken.objects.filter(subscription=subscription).order_by("-expires_at").first()
    )
    if latest and latest.expires_at > now + timedelta(hours=23, minutes=50):
        return  # cooldown; public response stays identical
    ConfirmationToken.objects.filter(subscription=subscription, consumed_at=None).update(
        expires_at=now
    )
    ConfirmationMessage.objects.filter(
        token__subscription=subscription,
        status=ConfirmationMessage.Status.PENDING,
    ).update(status=ConfirmationMessage.Status.CANCELLED)
    subscription.status = Subscription.Status.PENDING
    subscription.tracking_allowed = False
    subscription.save(update_fields=["status", "tracking_allowed", "updated_at"])
    evidence = ConsentEvidence.objects.create(
        subscription=subscription,
        action="requested",
        text_version=settings.NEWSLETTER_CONSENT_VERSION,
        text=settings.NEWSLETTER_CONSENT_TEXT,
        source="public_form",
        email_snapshot=contact.email,
        privacy_version=settings.NEWSLETTER_PRIVACY_VERSION,
        privacy_text=settings.NEWSLETTER_PRIVACY_TEXT,
        text_sha256=hashlib.sha256(settings.NEWSLETTER_CONSENT_TEXT.encode()).hexdigest(),
        remote_address=evidence_address(remote_address),
    )
    token = ConfirmationToken.objects.create(
        subscription=subscription,
        evidence=evidence,
        expires_at=now + timedelta(hours=24),
    )
    ConfirmationMessage.objects.create(
        token=token,
        recipient=contact.email,
        sender=settings.DEFAULT_FROM_EMAIL,
        subject="Newsletter-Anmeldung bestätigen",
        body_snapshot=render_to_string(
            "emails/confirmation.txt",
            {"link": "{{confirmation_link}}", "consent_text": evidence.text},
        ),
    )
    # Durable pending rows are picked up by Beat/management command; no broker call before commit.


@transaction.atomic
def confirm_subscription(value, remote_address=""):
    reference = decode_reference(value, "confirmation")
    token = ConfirmationToken.objects.filter(pk=reference).first() if reference else None
    if token is None:
        return False
    subscription = Subscription.objects.select_for_update().get(pk=token.subscription_id)
    token = ConfirmationToken.objects.select_for_update().get(pk=token.pk)
    now = timezone.now()
    if token.consumed_at:
        return subscription.status == Subscription.Status.ACTIVE
    if (
        token.expires_at <= now
        or Suppression.objects.filter(contact=subscription.contact_id).exists()
    ):
        return False
    token.consumed_at = now
    token.save(update_fields=["consumed_at"])
    subscription.status = Subscription.Status.ACTIVE
    subscription.save(update_fields=["status", "updated_at"])
    evidence = ConsentEvidence.objects.create(
        subscription=subscription,
        action="confirmed",
        text_version=token.evidence.text_version,
        text=token.evidence.text,
        source="confirmation_post",
        email_snapshot=token.evidence.email_snapshot,
        privacy_version=token.evidence.privacy_version,
        privacy_text=token.evidence.privacy_text,
        text_sha256=token.evidence.text_sha256,
        remote_address=evidence_address(remote_address),
        request_evidence=token.evidence,
        confirmation_reference=token.id,
    )
    ConsentEvent.objects.create(
        name="subscription.confirmed",
        subscription=subscription,
        cause_id=token.id,
    )
    return bool(evidence.pk)


@transaction.atomic
def unsubscribe(value, source="unsubscribe_post"):
    reference = decode_reference(value, "unsubscribe")
    subscription = (
        Subscription.objects.select_for_update().filter(pk=reference).first() if reference else None
    )
    if subscription is None:
        return False
    if subscription.status == Subscription.Status.UNSUBSCRIBED:
        return True
    subscription.status = Subscription.Status.UNSUBSCRIBED
    subscription.tracking_allowed = False
    subscription.save(update_fields=["status", "tracking_allowed", "updated_at"])
    latest = (
        ConsentEvidence.objects.filter(subscription=subscription).order_by("-occurred_at").first()
    )
    ConsentEvidence.objects.create(
        subscription=subscription,
        action="withdrawn",
        source=source,
        text_version=latest.text_version if latest else "unknown",
        text=latest.text if latest else "",
        email_snapshot=subscription.contact.email,
        privacy_version=latest.privacy_version if latest else "",
        privacy_text=latest.privacy_text if latest else "",
        text_sha256=latest.text_sha256 if latest else "",
        request_evidence=(latest.request_evidence or latest) if latest else None,
    )
    ConfirmationToken.objects.filter(subscription=subscription, consumed_at=None).update(
        expires_at=timezone.now()
    )
    ConfirmationMessage.objects.filter(
        token__subscription=subscription,
        status=ConfirmationMessage.Status.PENDING,
    ).update(status=ConfirmationMessage.Status.CANCELLED)
    ConsentEvent.objects.create(
        name="subscription.withdrawn",
        subscription=subscription,
        cause_id=subscription.id,
    )
    return True
