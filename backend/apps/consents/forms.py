from django import forms
from django.conf import settings


class SubscribeForm(forms.Form):
    email = forms.EmailField(label="E-Mail-Adresse", max_length=254)
    consent = forms.BooleanField(label="Newsletter abonnieren", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["consent"].label = settings.NEWSLETTER_CONSENT_TEXT
        self.privacy_text = settings.NEWSLETTER_PRIVACY_TEXT
