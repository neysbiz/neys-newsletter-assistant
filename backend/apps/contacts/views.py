from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import operator_required

from .forms import ImportConfirmForm, ImportUploadForm
from .imports import apply_import, cancel_import, create_import_preview
from .models import ImportBatch
from .selectors import contact_list, import_preview, recent_imports


@operator_required
def contacts(request):
    query = request.GET.get("q", "")[:254]
    return render(
        request, "management/contacts.html", {"contacts": contact_list(query), "q": query}
    )


@operator_required
@require_http_methods(["GET", "POST"])
def import_upload(request):
    form = ImportUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            batch = create_import_preview(
                form.cleaned_data["file"],
                form.cleaned_data["delimiter"],
                request.user,
                form.cleaned_data["active_export"],
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect("contact_import_preview", batch_id=batch.id)
    response = render(
        request,
        "management/import_upload.html",
        {"form": form, "batches": recent_imports(request.user)},
    )
    response["Cache-Control"] = "no-store"
    return response


@operator_required
@require_http_methods(["GET", "POST"])
def import_review(request, batch_id):
    batch = get_object_or_404(ImportBatch, pk=batch_id, owner=request.user)
    form = ImportConfirmForm(request.POST or None)
    if request.method == "POST":
        if request.POST.get("action") == "cancel":
            cancel_import(batch.id, request.user)
            return redirect("contact_import_upload")
        if form.is_valid():
            try:
                apply_import(batch.id, request.user)
            except ValidationError as error:
                form.add_error(None, error)
            else:
                return redirect("contact_import_preview", batch_id=batch.id)
    context = {"batch": batch, "form": form, **import_preview(batch)}
    response = render(request, "management/import_preview.html", context)
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "same-origin"
    return response
