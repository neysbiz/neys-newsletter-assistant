import hashlib
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.contacts.models import Suppression

from .models import ConfirmationMessage, Subscription
from .tokens import encode_reference


def send_confirmation(message_id):
    snapshot = ConfirmationMessage.objects.select_related("token").get(pk=message_id)
    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().get(
            pk=snapshot.token.subscription_id
        )
        message = (
            ConfirmationMessage.objects.select_for_update()
            .select_related(
                "token",
                "token__evidence",
                "token__subscription__contact",
            )
            .get(pk=message_id)
        )
        if message.status != ConfirmationMessage.Status.PENDING:
            return
        if (
            subscription.status != Subscription.Status.PENDING
            or message.token.expires_at <= timezone.now()
            or Suppression.objects.filter(contact_id=subscription.contact_id).exists()
        ):
            message.status = ConfirmationMessage.Status.CANCELLED
            message.save(update_fields=["status", "updated_at"])
            return
        link = settings.PUBLIC_BASE_URL + reverse(
            "confirm", args=[encode_reference(message.token_id, "confirmation")]
        )
        # Legacy pending rows have no snapshot; capture the actual message at first attempt.
        message.recipient = message.recipient or message.token.subscription.contact.email
        message.sender = message.sender or settings.DEFAULT_FROM_EMAIL
        message.subject = message.subject or "Newsletter-Anmeldung bestätigen"
        message.body_snapshot = message.body_snapshot or render_to_string(
            "emails/confirmation.txt",
            {"link": "{{confirmation_link}}", "consent_text": message.token.evidence.text},
        )
        content = message.body_snapshot.replace("{{confirmation_link}}", link)
        message.body_sha256 = hashlib.sha256(content.encode()).hexdigest()
        message.attempted_at = timezone.now()
        message.status = ConfirmationMessage.Status.SENDING
        message.save(
            update_fields=[
                "recipient",
                "sender",
                "subject",
                "body_snapshot",
                "body_sha256",
                "attempted_at",
                "status",
                "updated_at",
            ]
        )
    email = EmailMultiAlternatives(
        message.subject,
        content,
        message.sender,
        [message.recipient],
        headers={"Message-ID": f"<{message.message_id}@newsletter.local>"},
    )
    try:
        result = email.send(fail_silently=False)
        outcome = (
            ConfirmationMessage.Status.ACCEPTED
            if result == 1
            else ConfirmationMessage.Status.FAILED
        )
    except Exception:
        # A timeout may happen after acceptance. No automatic retry of ambiguous delivery.
        outcome = ConfirmationMessage.Status.UNCERTAIN
    ConfirmationMessage.objects.filter(
        pk=message_id, status=ConfirmationMessage.Status.SENDING
    ).update(
        status=outcome,
        updated_at=timezone.now(),
        accepted_at=timezone.now() if outcome == ConfirmationMessage.Status.ACCEPTED else None,
    )


def dispatch_confirmations(limit=20):
    # Worker crashes after claim must remain visible, never blindly re-send.
    ConfirmationMessage.objects.filter(
        status=ConfirmationMessage.Status.SENDING,
        updated_at__lt=timezone.now() - timedelta(minutes=10),
    ).update(status=ConfirmationMessage.Status.UNCERTAIN, updated_at=timezone.now())
    ids = list(
        ConfirmationMessage.objects.filter(status=ConfirmationMessage.Status.PENDING).values_list(
            "pk",
            flat=True,
        )[:limit]
    )
    for message_id in ids:
        send_confirmation(message_id)
    return len(ids)
