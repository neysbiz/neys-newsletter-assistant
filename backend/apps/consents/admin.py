from django.contrib import admin

from apps.accounts.admin import ReadOnlyAdmin

from .models import ConfirmationMessage, ConsentEvidence, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(ReadOnlyAdmin):
    list_display = ("contact", "status", "tracking_allowed", "updated_at")
    list_filter = ("status",)


@admin.register(ConsentEvidence)
class EvidenceAdmin(ReadOnlyAdmin):
    list_display = ("subscription", "action", "purpose", "text_version", "occurred_at")


@admin.register(ConfirmationMessage)
class MessageAdmin(ReadOnlyAdmin):
    list_display = ("id", "status", "updated_at")
    list_filter = ("status",)
