from django.contrib import admin

from .models import Contact, Suppression


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Contact)
class ContactAdmin(ReadOnlyAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email_key",)


@admin.register(Suppression)
class SuppressionAdmin(ReadOnlyAdmin):
    list_display = ("contact", "reason", "created_at")
