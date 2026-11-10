from dataclasses import dataclass

from bs4 import BeautifulSoup
from curl_cffi import requests

from src.services.recipe_image import find_page_image_url


@dataclass
class ScrapedPage:
    text: str
    image_url: str | None  # the page's main picture, if it declares one


def scrape_recipe_page(url: str) -> str:
    """Just the readable text of the page."""
    return scrape_recipe(url).text


def scrape_recipe(url: str) -> ScrapedPage:
    """Fetches the page once and returns both its readable text and its main image URL."""
    try:
        # Impersonate authentic Chrome TLS & HTTP/2 signatures
        response = requests.get(
            url,
            impersonate="chrome124",
            timeout=15,
            headers={
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        response.raise_for_status()
    except Exception as exc:
        raise ValueError(
            f"Failed to fetch recipe webpage: {exc}"
        ) from exc

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the image BEFORE the cleanup below: it deletes the <script> tags that hold the JSON-LD
    image_url = find_page_image_url(soup, str(getattr(response, "url", "") or url))

    # Strip script, style, navigation, ads, and structural elements
    for tag in soup(
        ["script", "style", "nav", "header", "footer", "aside", "form", "svg"]
    ):
        tag.decompose()

    lines = (line.strip() for line in soup.get_text(separator="\n").splitlines())
    clean_text = "\n".join(chunk for chunk in lines if chunk)

    if not clean_text:
        raise ValueError("Could not extract readable text from the provided URL.")

    return ScrapedPage(text=clean_text[:25000], image_url=image_url)