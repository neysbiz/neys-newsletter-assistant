from django.contrib import admin

from apps.accounts.admin import ReadOnlyAdmin

from .models import Asset, Campaign, CampaignRevision


@admin.register(Campaign)
class CampaignAdmin(ReadOnlyAdmin):
    list_display = ("subject", "updated_at")


@admin.register(CampaignRevision)
class RevisionAdmin(ReadOnlyAdmin):
    list_display = ("subject", "number", "created_at")


@admin.register(Asset)
class AssetAdmin(ReadOnlyAdmin):
    list_display = ("title", "width", "height", "created_at")
