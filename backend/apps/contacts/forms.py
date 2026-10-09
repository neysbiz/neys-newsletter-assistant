from django import forms


class ImportUploadForm(forms.Form):
    file = forms.FileField(label="Mailchimp-Export (UTF-8)")
    delimiter = forms.ChoiceField(
        label="Trennzeichen",
        choices=[(",", "Komma (CSV)"), (";", "Semikolon (CSV)"), ("\t", "Tabulator (TSV)")],
    )
    active_export = forms.BooleanField(
        label="Diese Datei enthält ausschließlich aktive Mailchimp-Abonnenten.",
        required=True,
    )


class ImportConfirmForm(forms.Form):
    confirm = forms.BooleanField(
        label=(
            "Ich habe die Vorschau geprüft und möchte die Kontakte ohne Versandfreigabe übernehmen."
        ),
        required=True,
    )
