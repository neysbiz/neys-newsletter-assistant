from django.contrib import admin

from apps.accounts.admin import ReadOnlyAdmin

from .models import ConfirmationMessage, ConfirmationToken, ConsentEvidence, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(ReadOnlyAdmin):
    list_display = ("contact", "status", "tracking_allowed", "updated_at")
    list_filter = ("status",)


@admin.register(ConsentEvidence)
class EvidenceAdmin(ReadOnlyAdmin):
    list_display = ("email_snapshot", "action", "purpose", "text_version", "occurred_at")
    list_filter = ("action", "purpose", "text_version")
    search_fields = ("email_snapshot", "subscription__contact__email_key")


@admin.register(ConfirmationToken)
class TokenAdmin(ReadOnlyAdmin):
    list_display = ("id", "subscription", "evidence", "expires_at", "consumed_at")


@admin.register(ConfirmationMessage)
class MessageAdmin(ReadOnlyAdmin):
    list_display = ("message_id", "recipient", "status", "attempted_at", "accepted_at")
    list_filter = ("status",)
