import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    file = models.FileField(upload_to="newsletter-images/")
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=200)
    preheader = models.CharField(max_length=200, blank=True)
    blocks = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)


class CampaignRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.PROTECT, related_name="revisions")
    number = models.PositiveIntegerField()
    subject = models.CharField(max_length=200)
    preheader = models.CharField(max_length=200, blank=True)
    blocks = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["campaign", "number"], name="unique_revision_number")
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Freigegebene Revisionen können nicht geändert werden.")
        return super().save(*args, **kwargs)


class RevisionAsset(models.Model):
    revision = models.ForeignKey(CampaignRevision, on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["revision", "asset"], name="unique_revision_asset")
        ]
