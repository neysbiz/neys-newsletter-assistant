import uuid

from django.db import models


class Subscription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Bestätigung ausstehend"
        ACTIVE = "active", "Aktiv"
        UNSUBSCRIBED = "unsubscribed", "Abgemeldet"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.OneToOneField("contacts.Contact", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Tracking is not activated by newsletter consent.
    tracking_allowed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["pending", "active", "unsubscribed"]),
                name="valid_subscription_status",
            )
        ]


class ConsentEvidence(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    action = models.CharField(
        max_length=20,
        choices=[
            ("requested", "Angefordert"),
            ("confirmed", "Bestätigt"),
            ("withdrawn", "Widerrufen"),
        ],
    )
    purpose = models.CharField(max_length=20, default="newsletter")
    text_version = models.CharField(max_length=80)
    text = models.TextField()
    source = models.CharField(max_length=40)
    occurred_at = models.DateTimeField(auto_now_add=True)


class ConfirmationToken(models.Model):
    # Links use this random reference plus purpose-specific server-side HMAC.
    # No complete bearer token or email address is persisted in a URL payload.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    evidence = models.OneToOneField(ConsentEvidence, on_delete=models.PROTECT)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)


class ConfirmationMessage(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ausstehend"
        SENDING = "sending", "Versand begonnen"
        ACCEPTED = "accepted", "Vom Adapter angenommen"
        FAILED = "failed", "Fehlgeschlagen"
        UNCERTAIN = "uncertain", "Ausgang unklar"
        CANCELLED = "cancelled", "Nicht mehr benötigt"

    token = models.OneToOneField(ConfirmationToken, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    updated_at = models.DateTimeField(auto_now=True)


class RateLimitBucket(models.Model):
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)


class ConsentEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80)
    version = models.PositiveSmallIntegerField(default=1)
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    cause_id = models.UUIDField()
    occurred_at = models.DateTimeField(auto_now_add=True)
