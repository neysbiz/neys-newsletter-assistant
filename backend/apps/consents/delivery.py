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
        message.status = ConfirmationMessage.Status.SENDING
        message.save(update_fields=["status", "updated_at"])
    link = settings.PUBLIC_BASE_URL + reverse(
        "confirm", args=[encode_reference(message.token_id, "confirmation")]
    )
    content = render_to_string("emails/confirmation.txt", {"link": link})
    email = EmailMultiAlternatives(
        "Newsletter-Anmeldung bestätigen",
        content,
        settings.DEFAULT_FROM_EMAIL,
        [message.token.subscription.contact.email],
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
