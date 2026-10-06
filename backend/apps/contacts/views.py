from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from .selectors import contact_list


@login_required
def contacts(request):
    if not request.user.is_active or not request.user.is_staff:
        raise PermissionDenied
    query = request.GET.get("q", "")[:254]
    return render(
        request, "management/contacts.html", {"contacts": contact_list(query), "q": query}
    )
