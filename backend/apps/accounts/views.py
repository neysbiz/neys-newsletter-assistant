from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


@login_required
def dashboard(request):
    if not request.user.is_active or not request.user.is_staff:
        raise PermissionDenied
    return render(request, "management/dashboard.html")
