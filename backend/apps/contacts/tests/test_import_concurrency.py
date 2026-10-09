from concurrent.futures import ThreadPoolExecutor

import pytest
from apps.contacts.imports import apply_import, create_import_preview
from apps.contacts.models import Contact, MailchimpRecord
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connection


@pytest.mark.postgresql
@pytest.mark.django_db(transaction=True)
def test_double_import_confirmation_commits_only_once(django_user_model):
    assert connection.vendor == "postgresql"
    actor = django_user_model.objects.create_user(username="parallel-importer", is_staff=True)
    batch = create_import_preview(
        SimpleUploadedFile("synthetic.csv", b"Emailadresse\none@example.com\n"),
        ",",
        actor,
        active_export=True,
    )

    def confirm(_):
        close_old_connections()
        try:
            return apply_import(batch.id, actor).result
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(confirm, range(2)))
    assert results[0] == results[1]
    assert Contact.objects.count() == 1
    assert MailchimpRecord.objects.count() == 1
