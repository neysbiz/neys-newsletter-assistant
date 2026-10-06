from concurrent.futures import ThreadPoolExecutor

import pytest
from apps.consents.models import ConfirmationMessage, ConfirmationToken, Subscription
from apps.consents.services import confirm_subscription, request_subscription
from apps.consents.tokens import encode_reference
from apps.contacts.models import Contact
from django.db import close_old_connections, connection

pytestmark = [pytest.mark.postgresql, pytest.mark.django_db(transaction=True)]


def test_concurrent_registration_and_confirmation_are_unique():
    assert connection.vendor == "postgresql", "Concurrency gate requires PostgreSQL"

    def register(_):
        close_old_connections()
        try:
            request_subscription("same@example.com", "192.0.2.1")
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(register, range(3)))
    assert Contact.objects.count() == 1
    assert ConfirmationMessage.objects.count() == 1
    token = encode_reference(ConfirmationToken.objects.get().id, "confirmation")

    def confirm(_):
        close_old_connections()
        try:
            return confirm_subscription(token)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as executor:
        assert all(executor.map(confirm, range(3)))
    assert Subscription.objects.get().status == "active"
