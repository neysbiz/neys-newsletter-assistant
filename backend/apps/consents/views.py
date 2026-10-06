from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import SubscribeForm
from .services import confirm_subscription, request_subscription, unsubscribe


@require_http_methods(["GET", "POST"])
def subscribe(request):
    form = SubscribeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        request_subscription(form.cleaned_data["email"], request.META.get("REMOTE_ADDR", "unknown"))
        return render(
            request,
            "public/result.html",
            {
                "message": (
                    "Falls eine Bestätigung erforderlich ist, erhältst du eine E-Mail. "
                    "Bitte prüfe dein Postfach."
                )
            },
        )
    return render(request, "public/subscribe.html", {"form": form})


@require_http_methods(["GET", "POST"])
def confirm(request, token):
    if request.method == "GET":
        return render(
            request,
            "public/action.html",
            {"heading": "Newsletter bestätigen", "button": "Anmeldung bestätigen"},
        )
    success = confirm_subscription(token)
    return render(
        request,
        "public/result.html",
        {
            "message": "Deine Anmeldung ist bestätigt."
            if success
            else "Dieser Bestätigungslink ist ungültig oder abgelaufen."
        },
        status=200 if success else 400,
    )


@require_http_methods(["GET", "POST"])
def unsubscribe_page(request, token):
    if request.method == "GET":
        return render(
            request,
            "public/action.html",
            {"heading": "Newsletter abmelden", "button": "Newsletter abmelden"},
        )
    success = unsubscribe(token)
    return render(
        request,
        "public/result.html",
        {
            "message": "Du bist vom Newsletter abgemeldet."
            if success
            else "Dieser Abmeldelink ist ungültig."
        },
        status=200 if success else 400,
    )


@csrf_exempt
@require_POST
def one_click_unsubscribe(request, token):
    # RFC 8058 mail-client POST has no browser CSRF cookie; the signed URL is its credential.
    if request.POST.get("List-Unsubscribe") != "One-Click":
        return HttpResponse(status=400)
    return HttpResponse(status=200 if unsubscribe(token, source="rfc8058_post") else 400)


@require_GET
def test_unsubscribe(request):
    return render(
        request,
        "public/result.html",
        {"message": "Dies ist ein Testlink. Es wurde kein Abonnement geändert."},
    )
