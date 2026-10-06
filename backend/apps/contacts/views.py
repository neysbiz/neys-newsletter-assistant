from django.shortcuts import render

from apps.accounts.decorators import operator_required

from .selectors import contact_list


@operator_required
def contacts(request):
    query = request.GET.get("q", "")[:254]
    return render(
        request, "management/contacts.html", {"contacts": contact_list(query), "q": query}
    )
