from celery import shared_task

from .delivery import dispatch_confirmations


@shared_task(ignore_result=True)
def dispatch_pending_confirmations():
    dispatch_confirmations()
