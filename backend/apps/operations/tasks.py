from celery import shared_task


@shared_task
def worker_probe():
    """Infrastructure probe only; never sends email."""
    return {"status": "ok"}
