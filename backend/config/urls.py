from apps.accounts.views import dashboard
from apps.operations.views import health
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("manage/", dashboard, name="dashboard"),
    path("health/", health, name="health"),
]
