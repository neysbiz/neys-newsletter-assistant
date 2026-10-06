from django import forms
from django.forms import formset_factory

from .models import Asset


class CampaignForm(forms.Form):
    subject = forms.CharField(label="Betreff", max_length=200)
    preheader = forms.CharField(label="Vorschautext", max_length=200, required=False)


class BlockForm(forms.Form):
    type = forms.ChoiceField(
        label="Inhalt",
        required=False,
        choices=[
            ("", "Kein neuer Block"),
            ("text", "Text"),
            ("image", "Bild"),
            ("link", "Link / Button"),
        ],
    )
    text = forms.CharField(
        label="Text oder Linkbeschriftung", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )
    asset = forms.ModelChoiceField(label="Bild", queryset=Asset.objects.none(), required=False)
    alt = forms.CharField(label="Bildbeschreibung", max_length=300, required=False)
    url = forms.URLField(
        label="Linkziel (HTTPS)", max_length=2000, required=False, assume_scheme="https"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = Asset.objects.order_by("title")
        self.fields["asset"].label_from_instance = lambda obj: obj.title

    def clean(self):
        data = super().clean()
        if not data.get("type") and any(data.get(k) for k in ["text", "asset", "alt", "url"]):
            raise forms.ValidationError("Bitte die Inhaltsart auswählen.")
        return data

    def to_block(self):
        data = self.cleaned_data
        kind = data["type"]
        if kind == "text":
            return {"type": kind, "text": data["text"]}
        if kind == "link":
            return {"type": kind, "label": data["text"], "url": data["url"]}
        return {
            "type": kind,
            "asset_id": str(data["asset"].id) if data["asset"] else None,
            "alt": data["alt"],
        }


BlockFormSet = formset_factory(
    BlockForm, extra=1, can_order=True, can_delete=True, max_num=20, validate_max=True
)


class AssetForm(forms.Form):
    title = forms.CharField(label="Bildname", max_length=120)
    image = forms.FileField(label="Bild (PNG oder JPEG, bis 8 MB)")


class TestMailForm(forms.Form):
    recipient = forms.EmailField(label="Testempfänger", max_length=254)
