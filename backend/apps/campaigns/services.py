import uuid
import warnings
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from .models import Asset, Campaign, CampaignRevision, RevisionAsset
from .validation import validate_blocks, validate_copy


def upload_asset(title, upload):
    if upload.size > 8 * 1024 * 1024:
        raise ValidationError("Das Bild darf maximal 8 MB groß sein.")
    if not title.strip() or len(title) > 120:
        raise ValidationError("Bitte einen Bildnamen angeben (maximal 120 Zeichen).")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                if image.format not in {"PNG", "JPEG"}:
                    raise ValidationError("Nur PNG und JPEG sind zugelassen.")
                if image.width * image.height > 20_000_000:
                    raise ValidationError("Das Bild ist zu groß (maximal 20 Megapixel).")
                image.load()
                width, height = image.size
                output = BytesIO()
                if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                    image.convert("RGBA").save(output, format="PNG")
                    extension = "png"
                else:
                    image.convert("RGB").save(output, format="JPEG", quality=90)
                    extension = "jpg"
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ValidationError("Das Bild ist ungültig oder zu groß.") from error
    if output.tell() > 8 * 1024 * 1024:
        raise ValidationError("Das aufbereitete Bild überschreitet 8 MB.")
    asset = Asset(title=title.strip(), width=width, height=height)
    asset.file.save(f"{uuid.uuid4()}.{extension}", ContentFile(output.getvalue()), save=True)
    return asset


@transaction.atomic
def save_draft(subject, preheader, blocks, campaign_id=None):
    subject = validate_copy(subject, 200).strip()
    if not subject or "\r" in subject or "\n" in subject:
        raise ValidationError("Betreff fehlt oder enthält einen Zeilenumbruch.")
    preheader = validate_copy(preheader, 200)
    blocks = validate_blocks(blocks)
    campaign = (
        Campaign.objects.select_for_update().get(pk=campaign_id) if campaign_id else Campaign()
    )
    campaign.subject = subject
    campaign.preheader = preheader
    campaign.blocks = blocks
    campaign.save()
    return campaign


@transaction.atomic
def freeze_revision(campaign_id):
    campaign = Campaign.objects.select_for_update().get(pk=campaign_id)
    blocks = validate_blocks(campaign.blocks)
    last = campaign.revisions.order_by("-number").first()
    revision = CampaignRevision.objects.create(
        campaign=campaign,
        number=last.number + 1 if last else 1,
        subject=campaign.subject,
        preheader=campaign.preheader,
        blocks=blocks,
    )
    ids = {block["asset_id"] for block in blocks if block["type"] == "image"}
    RevisionAsset.objects.bulk_create(
        [RevisionAsset(revision=revision, asset_id=id_) for id_ in ids]
    )
    return revision
