from dataclasses import dataclass
from urllib.parse import urljoin

from django.conf import settings
from django.template.loader import render_to_string

from .models import Asset
from .validation import PLACEHOLDER


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    text: str
    html: str


def render_revision(revision, *, email, unsubscribe_url):
    def personalize(value):
        return PLACEHOLDER.sub(lambda match: email, value)

    blocks = []
    for source in revision.blocks:
        block = dict(source)
        for field in ["text", "label", "alt"]:
            if field in block:
                block[field] = personalize(block[field])
        if block["type"] == "image":
            asset = Asset.objects.get(pk=block["asset_id"])
            block["url"] = urljoin(settings.PUBLIC_BASE_URL + "/", asset.file.url)
        blocks.append(block)
    context = {
        "blocks": blocks,
        "preheader": personalize(revision.preheader),
        "unsubscribe_url": unsubscribe_url,
    }
    return RenderedEmail(
        subject=personalize(revision.subject),
        text=render_to_string("emails/newsletter.txt", context),
        html=render_to_string("emails/newsletter.html", context),
    )
