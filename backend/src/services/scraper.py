from bs4 import BeautifulSoup
from curl_cffi import requests


def scrape_recipe_page(url: str) -> str:
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

    # Strip script, style, navigation, ads, and structural elements
    for tag in soup(
        ["script", "style", "nav", "header", "footer", "aside", "form", "svg"]
    ):
        tag.decompose()

    lines = (line.strip() for line in soup.get_text(separator="\n").splitlines())
    clean_text = "\n".join(chunk for chunk in lines if chunk)

    if not clean_text:
        raise ValueError("Could not extract readable text from the provided URL.")

    return clean_text[:25000]