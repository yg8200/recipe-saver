from unittest.mock import MagicMock, patch

import pytest

from src.services import scraper

HTML = """
<html><head>
<meta property="og:image" content="/photos/pie.jpg">
<script type="application/ld+json">{"@type": "Recipe", "image": "https://cdn.x.com/pie.jpg"}</script>
<script>var tracking = 1;</script></head>
<body><nav>menu</nav><h1>Apple pie</h1><p>Mix   flour</p><footer>bye</footer></body></html>
"""


def _page(html=HTML, url="https://x.com/pie"):
    response = MagicMock(text=html, url=url)
    return patch.object(scraper.requests, "get", return_value=response)


# The scraper returns the readable text (no scripts, nav or footer) together with the page's image.
def test_scrape_recipe_returns_text_and_image():
    with _page():
        page = scraper.scrape_recipe("https://x.com/pie")
    assert page.text == "Apple pie\nMix   flour"
    assert page.image_url == "https://cdn.x.com/pie.jpg"


# scrape_recipe_page is the text-only view of the same result.
def test_scrape_recipe_page_returns_only_text():
    with _page():
        assert scraper.scrape_recipe_page("https://x.com/pie") == "Apple pie\nMix   flour"


# A page without an image still scrapes fine, with image_url None.
def test_scrape_recipe_without_image():
    with _page("<html><body><p>Soup</p></body></html>"):
        assert scraper.scrape_recipe("https://x.com/soup").image_url is None


# Fetch failures and pages with no readable text become friendly ValueErrors.
def test_scrape_recipe_errors():
    with patch.object(scraper.requests, "get", side_effect=RuntimeError("boom")):
        with pytest.raises(ValueError, match="Failed to fetch"):
            scraper.scrape_recipe("https://x.com/pie")
    with _page("<html><script>x</script></html>"):
        with pytest.raises(ValueError, match="readable text"):
            scraper.scrape_recipe("https://x.com/pie")
