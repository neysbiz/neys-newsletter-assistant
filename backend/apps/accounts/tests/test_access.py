import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_anonymous_redirects_to_login(client):
    assert client.get(reverse("dashboard")).status_code == 302


@pytest.mark.django_db
def test_regular_account_cannot_manage(client, django_user_model):
    user = django_user_model.objects.create_user(username="reader", password="test")
    client.force_login(user)
    assert client.get(reverse("dashboard")).status_code == 403


@pytest.mark.django_db
def test_staff_can_manage_and_logout_requires_post(client, django_user_model):
    user = django_user_model.objects.create_user(username="operator", is_staff=True)
    client.force_login(user)
    assert client.get(reverse("dashboard")).status_code == 200
    assert client.get(reverse("logout")).status_code == 405
    assert client.post(reverse("logout")).status_code == 302
