import uuid

from django.conf import settings
from django.db import models


class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254)
    email_key = models.CharField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MailchimpRecord(models.Model):
    """Source snapshot, never a newsletter consent or account permission."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT)
    batch_id = models.UUIDField(db_index=True)
    source_status = models.CharField(max_length=20, default="subscribed")
    marketing_flag = models.BooleanField(null=True)
    leid = models.CharField(max_length=80, blank=True)
    euid = models.CharField(max_length=80, blank=True)
    source = models.CharField(max_length=254, blank=True)
    # Preserve original timestamp strings; do not invent a UTC interpretation.
    source_data = models.JSONField(default=dict)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch_id", "contact"], name="unique_import_contact"),
            models.CheckConstraint(
                condition=models.Q(source_status="subscribed"), name="active_mailchimp_source_only"
            ),
        ]


class ImportBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    filename = models.CharField(max_length=254)
    file_sha256 = models.CharField(max_length=64)
    delimiter = models.CharField(max_length=1)
    ignored_columns = models.JSONField(default=list)
    rows = models.JSONField(default=list)
    status = models.CharField(
        max_length=20,
        default="preview",
        choices=[("preview", "Vorschau"), ("completed", "Übernommen"), ("cancelled", "Verworfen")],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["preview", "completed", "cancelled"]),
                name="valid_import_batch_status",
            )
        ]


class Suppression(models.Model):
    contact = models.OneToOneField(Contact, on_delete=models.PROTECT)
    reason = models.CharField(
        max_length=40,
        choices=[
            ("hard_bounce", "Harter Rückläufer"),
            ("complaint", "Beschwerde"),
            ("manual", "Manuell"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
