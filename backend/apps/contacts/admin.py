from django.contrib import admin

from apps.accounts.admin import ReadOnlyAdmin

from .models import Contact, Suppression


@admin.register(Contact)
class ContactAdmin(ReadOnlyAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email_key",)


@admin.register(Suppression)
class SuppressionAdmin(ReadOnlyAdmin):
    list_display = ("contact", "reason", "created_at")
