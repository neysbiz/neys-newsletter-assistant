import pytest
from apps.operations.services import infrastructure_status
from apps.operations.tasks import worker_probe
from celery.contrib.testing.worker import start_worker
from config.celery import app

pytestmark = pytest.mark.infrastructure


@pytest.mark.django_db
def test_database_and_redis_are_reachable():
    assert infrastructure_status() == {"database": "ok", "redis": "ok", "status": "ok"}


def test_real_broker_and_worker_roundtrip():
    previous = app.conf.task_always_eager
    app.conf.task_always_eager = False
    try:
        with start_worker(app, perform_ping_check=False, pool="solo", shutdown_timeout=10):
            result = worker_probe.delay()
            assert result.get(timeout=10) == {"status": "ok"}
    finally:
        app.conf.task_always_eager = previous
