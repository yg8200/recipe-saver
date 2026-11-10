import json
import socket
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from src.services import recipe_image as ri
from src.services.image_store import delete_recipe_image, save_recipe_image
from src.services.recipe_image import download_image
from src.services.url_safety import is_public_http_url

BASE = "https://example.com/recipes/pie"


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _ld(data):
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


# ------------------------------------------------------------------ finding the image URL

# The Recipe's own JSON-LD image wins over the social-sharing image.
def test_find_image_prefers_recipe_json_ld():
    html = _ld({"@type": "Recipe", "image": "https://cdn.example.com/pie.jpg"}) + \
        '<meta property="og:image" content="https://cdn.example.com/og.jpg">'
    assert ri.find_page_image_url(_soup(html), BASE) == "https://cdn.example.com/pie.jpg"


# JSON-LD images can be lists or ImageObjects, and the Recipe may sit inside an @graph.
def test_find_image_handles_json_ld_shapes():
    graph = {"@graph": [{"@type": "WebSite"}, {"@type": ["Thing", "Recipe"],
                                                "image": [{"@type": "ImageObject", "url": "/img/pie.jpg"}]}]}
    assert ri.find_page_image_url(_soup(_ld(graph)), BASE) == "https://example.com/img/pie.jpg"


# Broken JSON-LD is skipped and og:image is used instead.
def test_find_image_falls_back_to_og_image_when_json_ld_is_broken():
    html = '<script type="application/ld+json">{not json</script>' \
           '<meta property="og:image" content="//cdn.example.com/og.jpg">'
    assert ri.find_page_image_url(_soup(html), BASE) == "https://cdn.example.com/og.jpg"


# twitter:image and link rel=image_src are used when nothing better exists.
def test_find_image_other_meta_sources():
    assert ri.find_page_image_url(_soup('<meta name="twitter:image" content="/t.jpg">'), BASE) == "https://example.com/t.jpg"
    assert ri.find_page_image_url(_soup('<link rel="image_src" href="/l.jpg">'), BASE) == "https://example.com/l.jpg"


# A page that declares no image gives None (also for empty or non-Recipe JSON-LD).
def test_find_image_returns_none_when_page_has_no_image():
    html = _ld({"@type": "Article", "image": "x.jpg"}) + _ld({"@type": "Recipe", "image": ""}) + \
        _ld({"@type": "Recipe", "image": 123}) + \
        '<meta property="og:image" content="   ">'
    assert ri.find_page_image_url(_soup(html), BASE) is None
    assert ri.find_page_image_url(_soup("<p>hi</p>"), BASE) is None


# YouTube thumbnails are tried best quality first.
def test_youtube_thumbnail_urls():
    urls = ri.youtube_thumbnail_urls("abc123")
    assert urls[0].endswith("/vi/abc123/maxresdefault.jpg")
    assert urls[1].endswith("/vi/abc123/mqdefault.jpg")


# ------------------------------------------------------------------ downloading

def _response(status=200, content=b"img", content_type="image/jpeg", location=None):
    response = MagicMock(status_code=status, content=content)
    response.headers = {"content-type": content_type, **({"location": location} if location else {})}
    return response


@pytest.fixture
def public(monkeypatch):
    """Treat every URL as public so download tests don't need DNS."""
    monkeypatch.setattr(ri, "is_public_http_url", lambda url: True)


# A normal image response is returned as bytes.
def test_download_image_success(public):
    with patch.object(ri.requests, "get", return_value=_response()):
        assert download_image("https://x.com/a.jpg") == b"img"


# Non-200 answers, non-image content types and oversized files all give None.
@pytest.mark.parametrize("response", [
    _response(status=404), _response(content_type="text/html"),
    _response(content=b"x" * (ri.MAX_DOWNLOAD_BYTES + 1)),
])
def test_download_image_rejects_bad_responses(public, response):
    with patch.object(ri.requests, "get", return_value=response):
        assert download_image("https://x.com/a.jpg") is None


# A redirect is followed (each hop is checked) until the image is reached.
def test_download_image_follows_redirect(public):
    replies = [_response(status=302, location="/final.jpg"), _response()]
    with patch.object(ri.requests, "get", side_effect=replies) as get:
        assert download_image("https://x.com/a.jpg") == b"img"
    assert get.call_args.args[0] == "https://x.com/final.jpg"


# Endless redirects stop after a few hops instead of looping forever.
def test_download_image_gives_up_on_redirect_loop(public):
    with patch.object(ri.requests, "get", return_value=_response(status=302, location="/again")):
        assert download_image("https://x.com/a.jpg") is None


# A URL that isn't public is never requested at all.
def test_download_image_skips_non_public_urls():
    with patch.object(ri.requests, "get") as get:
        assert download_image("http://127.0.0.1:5432/secret") is None
    get.assert_not_called()


# A network error gives None instead of raising.
def test_download_image_network_error_returns_none(public):
    with patch.object(ri.requests, "get", side_effect=RuntimeError("timeout")):
        assert download_image("https://x.com/a.jpg") is None


# ------------------------------------------------------------------ fetch_and_store_image

# Candidates are tried in order: empty ones and failed downloads are skipped, the first real image is stored.
def test_fetch_and_store_image_uses_first_usable_candidate(app, jpeg_bytes, monkeypatch):
    downloads = {"https://x.com/dead.jpg": None, "https://x.com/html.jpg": b"<html>", "https://x.com/ok.jpg": jpeg_bytes}
    monkeypatch.setattr(ri, "download_image", lambda url: downloads[url])
    with app.app_context():
        name = ri.fetch_and_store_image([None, "https://x.com/dead.jpg", "https://x.com/html.jpg", "https://x.com/ok.jpg"])
    assert name.endswith(".jpg")


# With no usable candidate the result is None, and an unexpected storage error is swallowed.
def test_fetch_and_store_image_returns_none_on_failure(app, jpeg_bytes, monkeypatch):
    with app.app_context():
        assert ri.fetch_and_store_image([None]) is None
        monkeypatch.setattr(ri, "download_image", lambda url: jpeg_bytes)
        with patch.object(ri, "save_recipe_image", side_effect=OSError("disk full")):
            assert ri.fetch_and_store_image(["https://x.com/a.jpg"]) is None


# ------------------------------------------------------------------ url_safety

# Loopback, private, link-local, non-http and host-less URLs are refused.
@pytest.mark.parametrize("url", [
    "http://127.0.0.1/a.jpg", "http://10.0.0.5/a.jpg", "http://192.168.1.1/a.jpg",
    "http://169.254.169.254/latest/meta-data", "http://[::1]/a.jpg",
    "ftp://example.com/a.jpg", "file:///etc/passwd", "http:///nohost",
])
def test_is_public_http_url_rejects_internal_and_odd_urls(url):
    assert is_public_http_url(url) is False


# A public address is allowed; a name that doesn't resolve is refused.
def test_is_public_http_url_allows_public_and_rejects_unresolvable():
    assert is_public_http_url("https://8.8.8.8/a.jpg") is True
    with patch("src.services.url_safety.socket.getaddrinfo", side_effect=socket.gaierror):
        assert is_public_http_url("https://does-not-exist.invalid/a.jpg") is False


# A hostname that resolves to a private address is refused (the classic SSRF trick).
def test_is_public_http_url_rejects_name_resolving_to_private_ip():
    with patch("src.services.url_safety.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("10.1.2.3", 0))]):
        assert is_public_http_url("https://innocent.example.com/a.jpg") is False


# ------------------------------------------------------------------ image_store

# Odd or missing names are ignored when deleting; real files are removed.
def test_delete_recipe_image_ignores_bad_names_and_removes_real_files(app, jpeg_bytes):
    with app.app_context():
        name = save_recipe_image(jpeg_bytes)
        delete_recipe_image(None)
        delete_recipe_image("../../etc/passwd")
        delete_recipe_image("missing.jpg")
        delete_recipe_image(name)
        import os
        assert os.listdir(app.config["UPLOAD_FOLDER"]) == []


# Saving rejects bytes that are not an image, including absurdly large pixel dimensions.
def test_save_recipe_image_rejects_invalid_and_bomb_images(app):
    from PIL import Image

    with app.app_context():
        with pytest.raises(ValueError):
            save_recipe_image(b"nope")
        with patch("src.utils.image_processing.Image.open", side_effect=Image.DecompressionBombError("big")):
            with pytest.raises(ValueError):
                save_recipe_image(b"whatever")
