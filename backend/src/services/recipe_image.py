"""Finds the dish photo of an online recipe, downloads it and stores it.

No AI is involved on purpose: recipe sites and YouTube already publish which picture represents
the page (JSON-LD "image", og:image, video thumbnail). Reading that metadata is free, instant and
can't hallucinate, whereas asking a language model to "find the photo" would be slower, cost money
and could invent a URL.
"""
import json
import logging
from urllib.parse import urljoin

from curl_cffi import requests

from src.services.image_store import save_recipe_image
from src.services.url_safety import is_public_http_url

logger = logging.getLogger(__name__)

MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024
MAX_REDIRECTS = 3


# --------------------------------------------------------------------------- finding the URL

def _first_image_url(value) -> str | None:
    """JSON-LD writes an image as a string, a list, or an ImageObject {"url": ...}."""
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        for item in value:
            found = _first_image_url(item)
            if found:
                return found
    if isinstance(value, dict):
        return _first_image_url(value.get("url"))
    return None


def _is_recipe_node(node: dict) -> bool:
    node_type = node.get("@type")
    types = node_type if isinstance(node_type, list) else [node_type]
    return "Recipe" in types


def _walk_json_ld(data):
    """Yields every dict in a JSON-LD document, including those inside @graph and lists."""
    if isinstance(data, list):
        for item in data:
            yield from _walk_json_ld(item)
    elif isinstance(data, dict):
        yield data
        yield from _walk_json_ld(data.get("@graph"))


def find_page_image_url(soup, base_url: str) -> str | None:
    """Best image for the page: the Recipe's own image first, then the social-sharing image."""
    candidates: list[str | None] = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except ValueError:
            continue
        for node in _walk_json_ld(data):
            if _is_recipe_node(node):
                candidates.append(_first_image_url(node.get("image")))

    for attrs in ({"property": "og:image"}, {"property": "og:image:secure_url"}, {"name": "twitter:image"}):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            candidates.append(tag["content"].strip())

    link = soup.find("link", rel="image_src")
    if link and link.get("href"):
        candidates.append(link["href"].strip())

    for candidate in candidates:
        if candidate:
            # Pages often use relative ("/img/x.jpg") or protocol-relative ("//cdn...") URLs
            return urljoin(base_url, candidate)
    return None


def youtube_thumbnail_urls(video_id: str) -> list[str]:
    """Best first: maxresdefault is 1280x720 but missing for some videos; mqdefault always exists."""
    base = f"https://i.ytimg.com/vi/{video_id}"
    return [f"{base}/maxresdefault.jpg", f"{base}/mqdefault.jpg"]


# --------------------------------------------------------------------------- downloading

def download_image(url: str) -> bytes | None:
    """Downloads an image, or returns None. Never raises: a missing photo must not break a save."""
    try:
        # Redirects are followed by hand so every hop can be checked (a public URL may redirect
        # to an internal address).
        for _ in range(MAX_REDIRECTS + 1):
            if not is_public_http_url(url):
                return None
            response = requests.get(
                url, impersonate="chrome124", timeout=10, allow_redirects=False,
                headers={"Accept": "image/*"},
            )
            if 300 <= response.status_code < 400 and response.headers.get("location"):
                url = urljoin(url, response.headers["location"])
                continue
            if response.status_code != 200:
                return None
            if not response.headers.get("content-type", "").lower().startswith("image/"):
                return None
            if len(response.content) > MAX_DOWNLOAD_BYTES:
                return None
            return response.content
    except Exception:
        logger.warning("Could not download image %s", url, exc_info=True)
    return None


def fetch_and_store_image(candidate_urls: list[str | None]) -> str | None:
    """Tries each URL in order and returns the stored file name of the first usable image."""
    for url in candidate_urls:
        if not url:
            continue
        data = download_image(url)
        if not data:
            continue
        try:
            return save_recipe_image(data)
        except ValueError:
            continue  # downloaded something that is not a real image; try the next candidate
        except Exception:
            logger.warning("Could not store image from %s", url, exc_info=True)
    return None
