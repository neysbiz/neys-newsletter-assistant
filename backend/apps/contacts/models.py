import uuid

from django.db import models


class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254)
    email_key = models.CharField(max_length=254, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


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
