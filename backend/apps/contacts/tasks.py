from celery import shared_task

from .imports import discard_expired_previews


@shared_task
def clear_expired_import_previews():
    return discard_expired_previews()
