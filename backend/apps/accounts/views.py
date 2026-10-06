from django.shortcuts import render

from apps.accounts.decorators import operator_required


@operator_required
def dashboard(request):
    return render(request, "management/dashboard.html")
