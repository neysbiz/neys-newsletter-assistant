from django.urls import path

from . import views

urlpatterns = [
    path("", views.campaigns, name="campaigns"),
    path("new/", views.edit_campaign, name="campaign_new"),
    path("assets/", views.assets, name="assets"),
    path("<uuid:campaign_id>/", views.edit_campaign, name="campaign_edit"),
    path("<uuid:campaign_id>/approve/", views.approve, name="campaign_approve"),
    path("revision/<uuid:revision_id>/", views.revision, name="revision"),
    path("revision/<uuid:revision_id>/preview/", views.preview, name="revision_preview"),
    path("revision/<uuid:revision_id>/test/", views.test_mail, name="revision_test"),
]
