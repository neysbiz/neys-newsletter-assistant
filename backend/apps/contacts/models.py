import uuid

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
