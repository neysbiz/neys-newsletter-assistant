from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .services import infrastructure_status


@require_GET
def health(request):
    status = infrastructure_status()
    return JsonResponse(status, status=200 if status["status"] == "ok" else 503)
