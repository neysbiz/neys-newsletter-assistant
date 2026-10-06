from django.conf import settings
from django.db import connection
from redis import Redis


def infrastructure_status():
    status = {"database": "ok", "redis": "ok"}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        status["database"] = "unavailable"
    try:
        Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1).ping()
    except Exception:
        status["redis"] = "unavailable"
    status["status"] = "ok" if all(v == "ok" for v in status.values()) else "unavailable"
    return status
