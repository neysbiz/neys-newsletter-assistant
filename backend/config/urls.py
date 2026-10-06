from apps.accounts.views import dashboard
from apps.consents import views as consent_views
from apps.contacts.views import contacts
from apps.operations.views import health
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", consent_views.subscribe, name="subscribe"),
    path("confirm/<str:token>/", consent_views.confirm, name="confirm"),
    path("unsubscribe/<str:token>/", consent_views.unsubscribe_page, name="unsubscribe"),
    path(
        "unsubscribe/one-click/<str:token>/",
        consent_views.one_click_unsubscribe,
        name="one_click_unsubscribe",
    ),
    path("manage/contacts/", contacts, name="contacts"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("manage/", dashboard, name="dashboard"),
    path("health/", health, name="health"),
]
