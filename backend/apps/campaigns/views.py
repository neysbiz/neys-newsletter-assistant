from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import operator_required

from .forms import AssetForm, BlockFormSet, CampaignForm, TestMailForm
from .models import Asset, Campaign, CampaignRevision
from .rendering import render_revision
from .selectors import campaign_list
from .services import freeze_revision, save_draft, upload_asset
from .testing import send_test_mail


@operator_required
def campaigns(request):
    return render(request, "management/campaigns.html", {"campaigns": campaign_list()})


@operator_required
def edit_campaign(request, campaign_id=None):
    campaign = get_object_or_404(Campaign, pk=campaign_id) if campaign_id else None
    initial = []
    if campaign:
        for index, block in enumerate(campaign.blocks):
            initial.append(
                {
                    "type": block["type"],
                    "text": block.get("text", block.get("label", "")),
                    "url": block.get("url", ""),
                    "alt": block.get("alt", ""),
                    "asset": block.get("asset_id"),
                    "ORDER": index + 1,
                }
            )
    form = CampaignForm(
        request.POST if request.method == "POST" else None,
        initial={"subject": campaign.subject, "preheader": campaign.preheader} if campaign else {},
    )
    blocks = BlockFormSet(
        request.POST if request.method == "POST" else None, initial=initial, prefix="blocks"
    )
    if request.method == "POST" and form.is_valid() and blocks.is_valid():
        content = [
            block.to_block() for block in blocks.ordered_forms if block.cleaned_data.get("type")
        ]
        try:
            saved = save_draft(
                form.cleaned_data["subject"],
                form.cleaned_data["preheader"],
                content,
                campaign_id=campaign.id if campaign else None,
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Entwurf gespeichert.")
            return redirect("campaign_edit", campaign_id=saved.pk)
    return render(
        request,
        "management/campaign_edit.html",
        {"form": form, "blocks": blocks, "campaign": campaign},
    )


@operator_required
@require_POST
def approve(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    try:
        revision = freeze_revision(campaign.pk)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
        return redirect("campaign_edit", campaign_id=campaign.pk)
    return redirect("revision", revision_id=revision.pk)


@operator_required
def revision(request, revision_id):
    frozen = get_object_or_404(CampaignRevision, pk=revision_id)
    return render(request, "management/revision.html", {"revision": frozen, "form": TestMailForm()})


@operator_required
def preview(request, revision_id):
    frozen = get_object_or_404(CampaignRevision, pk=revision_id)
    result = render_revision(
        frozen,
        email="vorschau@example.com",
        unsubscribe_url=settings.PUBLIC_BASE_URL + "/test-unsubscribe/",
    )
    response = HttpResponse(result.html)
    response["Content-Security-Policy"] = (
        "default-src 'none'; img-src 'self' https:; style-src 'unsafe-inline'"
    )
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


@operator_required
@require_POST
def test_mail(request, revision_id):
    frozen = get_object_or_404(CampaignRevision, pk=revision_id)
    form = TestMailForm(request.POST)
    if form.is_valid():
        try:
            accepted = send_test_mail(frozen, form.cleaned_data["recipient"])
        except Exception:
            messages.error(
                request,
                "Testversand fehlgeschlagen oder Ausgang unklar. Vor erneutem Versand prüfen.",
            )
        else:
            messages.success(
                request,
                "Testmail vom Versandadapter angenommen."
                if accepted
                else "Testmail nicht angenommen.",
            )
        return redirect("revision", revision_id=frozen.pk)
    return render(
        request, "management/revision.html", {"revision": frozen, "form": form}, status=400
    )


@operator_required
def assets(request):
    form = AssetForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            upload_asset(form.cleaned_data["title"], form.cleaned_data["image"])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Bild gespeichert.")
            return redirect("assets")
    return render(
        request,
        "management/assets.html",
        {"form": form, "assets": Asset.objects.order_by("-created_at")[:100]},
    )
