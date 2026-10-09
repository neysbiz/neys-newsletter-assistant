from apps.accounts.views import dashboard
from apps.consents import views as consent_views
from apps.contacts.views import contacts, import_review, import_upload
from apps.operations.views import health
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("test-unsubscribe/", consent_views.test_unsubscribe, name="test_unsubscribe"),
    path("manage/campaigns/", include("apps.campaigns.urls")),
    path("", consent_views.subscribe, name="subscribe"),
    path("confirm/<str:token>/", consent_views.confirm, name="confirm"),
    path("unsubscribe/<str:token>/", consent_views.unsubscribe_page, name="unsubscribe"),
    path(
        "unsubscribe/one-click/<str:token>/",
        consent_views.one_click_unsubscribe,
        name="one_click_unsubscribe",
    ),
    path("manage/contacts/", contacts, name="contacts"),
    path("manage/contacts/import/", import_upload, name="contact_import_upload"),
    path("manage/contacts/import/<uuid:batch_id>/", import_review, name="contact_import_preview"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("manage/", dashboard, name="dashboard"),
    path("health/", health, name="health"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
