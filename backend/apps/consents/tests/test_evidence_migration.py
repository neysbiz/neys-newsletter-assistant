import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


@pytest.mark.django_db(transaction=True)
def test_existing_jobs_migrate_with_distinct_ids_without_inventing_evidence():
    old = [("consents", "0001_initial"), ("contacts", "0001_initial")]
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    executor.migrate(old)
    try:
        apps = executor.loader.project_state(old).apps
        Contact = apps.get_model("contacts", "Contact")
        Subscription = apps.get_model("consents", "Subscription")
        Evidence = apps.get_model("consents", "ConsentEvidence")
        Token = apps.get_model("consents", "ConfirmationToken")
        Message = apps.get_model("consents", "ConfirmationMessage")
        for number in range(2):
            email = f"legacy{number}@example.com"
            contact = Contact.objects.create(email=email, email_key=email)
            subscription = Subscription.objects.create(contact=contact)
            evidence = Evidence.objects.create(
                subscription=subscription,
                action="requested",
                text_version="legacy-v1",
                text="Legacy consent text",
                source="public_form",
            )
            token = Token.objects.create(
                subscription=subscription,
                evidence=evidence,
                expires_at=timezone.now(),
            )
            Message.objects.create(token=token)
        MigrationExecutor(connection).migrate(latest)
        from apps.consents.models import ConfirmationMessage, ConsentEvidence

        ids = list(ConfirmationMessage.objects.values_list("message_id", flat=True))
        assert len(ids) == 2
        assert len(set(ids)) == 2
        assert all(ids)
        assert not ConsentEvidence.objects.exclude(email_snapshot="").exists()
        assert not ConsentEvidence.objects.exclude(privacy_text="").exists()
        assert not ConfirmationMessage.objects.exclude(accepted_at=None).exists()
    finally:
        MigrationExecutor(connection).migrate(latest)
