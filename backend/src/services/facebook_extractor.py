import urllib.parse
from dataclasses import dataclass

import yt_dlp

from src.services.ai_client import get_openai_client, get_openai_model
from src.services.youtube_extractor import _attempt_ai_extraction

FACEBOOK_HOSTS = ("facebook.com", "fb.watch")


@dataclass
class FacebookPost:
    caption: str
    thumbnail_url: str | None


def is_facebook_url(url: str) -> bool:
    """True for facebook.com (and its www/m/web subdomains) and fb.watch, but not lookalikes like notfacebook.com."""
    hostname = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(hostname == host or hostname.endswith("." + host) for host in FACEBOOK_HOSTS)


def get_facebook_post(url: str) -> FacebookPost:
    """Reads the caption and thumbnail of a public Facebook video/Reel with yt-dlp (no login)."""
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        # Private posts, login walls and Facebook blocking scrapers all end up here
        raise ValueError(
            "Could not read this Facebook post. It may be private, or Facebook blocked the request."
        ) from e
    return FacebookPost(caption=info.get("description") or "", thumbnail_url=info.get("thumbnail"))


def extract_recipe_from_facebook_caption(caption: str) -> dict:
    """Same idea as the YouTube description step. There is no transcript fallback on Facebook,
    so the recipe has to be written in the caption."""
    client = get_openai_client()
    model = get_openai_model("OPENAI_YOUTUBE_MODEL", default="gpt-4o")
    result = _attempt_ai_extraction(caption, client, model, source="the caption of a Facebook video")
    if not result["ingredients"] or not result["instructions"]:
        raise ValueError(
            "Could not find a complete recipe in the Facebook post caption. "
            "Only recipes written in the caption are supported."
        )
    return result
