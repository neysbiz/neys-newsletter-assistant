from django.contrib import admin

from apps.accounts.admin import ReadOnlyAdmin

from .models import Contact, ImportBatch, MailchimpRecord, Suppression


@admin.register(Contact)
class ContactAdmin(ReadOnlyAdmin):
    list_display = ("email", "first_name", "last_name", "created_at")
    search_fields = ("email_key", "first_name", "last_name")


@admin.register(MailchimpRecord)
class MailchimpRecordAdmin(ReadOnlyAdmin):
    list_display = ("contact", "source_status", "marketing_flag", "batch_id", "imported_at")
    list_filter = ("source_status", "marketing_flag")


@admin.register(ImportBatch)
class ImportBatchAdmin(ReadOnlyAdmin):
    list_display = ("id", "owner", "status", "created_at", "completed_at")
    list_filter = ("status",)


@admin.register(Suppression)
class SuppressionAdmin(ReadOnlyAdmin):
    list_display = ("contact", "reason", "created_at")
