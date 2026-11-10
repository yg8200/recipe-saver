from unittest.mock import patch

import pytest

from src.api.extract_recipe import validate_extracted_recipe
from src.schemas.recipe_schema import RecipeExtracted
from src.services.scraper import ScrapedPage
from src.services.youtube_extractor import get_youtube_video_id, is_youtube_url


# The validator accepts the Pydantic model returned by the website extractor and trims the title.
def test_validate_accepts_pydantic_model_from_url_extractor():
    model = RecipeExtracted(
        title="  Pancakes ", ingredients=["flour"], instructions=["mix"], prep_time_minutes=5
    )
    result = validate_extracted_recipe(model)
    assert result["title"] == "Pancakes"
    assert result["prep_time_minutes"] == 5


# The validator accepts prep_time/cook_time keys, drops blank lines, and nulls out bool/negative numbers.
def test_validate_accepts_short_time_keys_and_drops_bad_numbers():
    result = validate_extracted_recipe({
        "title": "Soup", "ingredients": ["water", " ", None], "instructions": ["boil"],
        "prep_time": 10, "cook_time": True, "servings": -2,
    })
    assert result["ingredients"] == ["water"]
    assert result["prep_time_minutes"] == 10
    assert result["cook_time_minutes"] is None
    assert result["servings"] is None


# The validator rejects a recipe whose ingredients are only blank strings.
def test_validate_rejects_whitespace_only_ingredients():
    with pytest.raises(ValueError):
        validate_extracted_recipe({"title": "x", "ingredients": ["  "], "instructions": ["a"]})


# Video ids are extracted from watch, youtu.be, shorts and embed links (ignoring extra parameters).
@pytest.mark.parametrize("url, expected", [
    ("https://www.youtube.com/watch?v=abc123&t=10", "abc123"),
    ("https://youtu.be/abc123?si=xyz", "abc123"),
    ("https://youtube.com/shorts/abc123", "abc123"),
    ("https://m.youtube.com/embed/abc123", "abc123"),
])
# Video ids are extracted from watch, youtu.be, shorts and embed links (ignoring extra parameters).
def test_get_youtube_video_id(url, expected):
    assert get_youtube_video_id(url) == expected


# YouTube links without a video id raise a ValueError instead of crashing.
@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?list=abc", "https://www.youtube.com/", "https://youtu.be/",
])
# YouTube links without a video id raise a ValueError instead of crashing.
def test_get_youtube_video_id_invalid(url):
    with pytest.raises(ValueError):
        get_youtube_video_id(url)


# Only real YouTube domains are detected; lookalikes or 'youtube.com' in the query are not.
def test_is_youtube_url_does_not_match_lookalike_domains():
    assert is_youtube_url("https://youtu.be/abc")
    assert not is_youtube_url("https://notyoutube.com/watch?v=abc")
    assert not is_youtube_url("https://example.com/?ref=youtube.com")


# Extracting from a website URL scrapes the page, runs the AI extractor and saves the recipe (201).
def test_extract_from_webpage_saves_recipe(client):
    model = RecipeExtracted(title="Web Cake", ingredients=["sugar"], instructions=["bake"], cook_time_minutes=30)
    with patch("src.api.extract_recipe.scrape_recipe", return_value=ScrapedPage("page text", None)), \
         patch("src.api.extract_recipe.extract_recipe_from_text", return_value=model):
        response = client.post("/recipes/extract", json={"url": "https://example.com/cake"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Web Cake"
    assert body["cook_time_minutes"] == 30


# YouTube URLs go to the YouTube extractor, not the website scraper.
def test_extract_routes_youtube_urls(client):
    data = {"has_recipe": True, "title": "YT Salad", "ingredients": ["lettuce"], "instructions": ["toss"]}
    with patch("src.api.extract_recipe.extract_recipe_from_youtube", return_value=data) as yt, \
         patch("src.api.extract_recipe.scrape_recipe") as scraper:
        response = client.post("/recipes/extract", json={"url": "https://youtu.be/abc"})
    assert response.status_code == 201
    yt.assert_called_once()
    scraper.assert_not_called()


# A non-JSON body, a JSON list, or an empty url returns 400.
@pytest.mark.parametrize("kwargs", [{"data": "not json"}, {"json": ["a list"]}, {"json": {"url": ""}}])
def test_extract_rejects_bad_body(client, kwargs):
    response = client.post("/recipes/extract", **kwargs)
    assert response.status_code == 400


WEB_RECIPE = RecipeExtracted(title="Web Cake", ingredients=["sugar"], instructions=["bake"])


# The validator rejects AI output that isn't a dict or is missing a title, ingredients or instructions.
@pytest.mark.parametrize("data, message", [
    ("not a dict", "valid JSON object"),
    ({"ingredients": ["a"], "instructions": ["b"]}, "title"),
    ({"title": "   ", "ingredients": ["a"], "instructions": ["b"]}, "title"),
    ({"title": "x", "ingredients": "a", "instructions": ["b"]}, "ingredients"),
    ({"title": "x", "ingredients": ["a"]}, "instructions"),
    ({"title": "x", "ingredients": ["a"], "instructions": [None, " "]}, "instructions"),
])
# The validator rejects AI output that isn't a dict or is missing a title, ingredients or instructions.
def test_validate_rejects_invalid_ai_output(data, message):
    with pytest.raises(ValueError, match=message):
        validate_extracted_recipe(data)


# Titles longer than the database limit are cut to 255 characters.
def test_validate_truncates_long_titles():
    result = validate_extracted_recipe({"title": "x" * 300, "ingredients": ["a"], "instructions": ["b"]})
    assert len(result["title"]) == 255


# Whitespace around the URL is stripped before scraping.
def test_extract_trims_url_before_scraping(client):
    with patch("src.api.extract_recipe.scrape_recipe", return_value=ScrapedPage("page", None)) as scraper, \
         patch("src.api.extract_recipe.extract_recipe_from_text", return_value=WEB_RECIPE):
        response = client.post("/recipes/extract", json={"url": "  https://example.com/cake  "})

    assert response.status_code == 201
    scraper.assert_called_once_with("https://example.com/cake")


# Extracting a recipe whose title already exists (case-insensitive) returns 409.
def test_extract_duplicate_title_returns_409(client):
    client.post("/recipes", json={"title": "web cake", "ingredients": ["a"], "instructions": ["b"]})

    with patch("src.api.extract_recipe.scrape_recipe", return_value=ScrapedPage("page", None)), \
         patch("src.api.extract_recipe.extract_recipe_from_text", return_value=WEB_RECIPE):
        response = client.post("/recipes/extract", json={"url": "https://example.com/cake"})

    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]


# A page that can't be fetched returns 400 with the scraper's error message.
def test_extract_scraper_failure_returns_400(client):
    with patch("src.api.extract_recipe.scrape_recipe",
               side_effect=ValueError("Failed to fetch recipe webpage: 404")):
        response = client.post("/recipes/extract", json={"url": "https://example.com/missing"})

    assert response.status_code == 400
    assert "Failed to fetch" in response.get_json()["error"]


# An extraction with no ingredients returns 400 and nothing is saved.
def test_extract_ai_output_without_ingredients_returns_400_and_saves_nothing(client):
    empty = {"title": "Not a recipe", "ingredients": [], "instructions": ["b"]}
    with patch("src.api.extract_recipe.extract_recipe_from_youtube", return_value=empty):
        response = client.post("/recipes/extract", json={"url": "https://youtu.be/abc"})

    assert response.status_code == 400
    assert "ingredients" in response.get_json()["error"]
    assert client.get("/recipes").get_json() == []


# Errors from the YouTube extractor (e.g. no transcript) return 400 with their message.
def test_extract_youtube_error_returns_400(client):
    with patch("src.api.extract_recipe.extract_recipe_from_youtube",
               side_effect=ValueError("No recipe found in the description, and the transcript is unavailable.")):
        response = client.post("/recipes/extract", json={"url": "https://www.youtube.com/watch?v=abc"})

    assert response.status_code == 400
    assert "transcript" in response.get_json()["error"]


# A YouTube link with no video id returns 400 before any AI call is made.
def test_extract_invalid_youtube_link_returns_400_without_ai_call(client):
    response = client.post("/recipes/extract", json={"url": "https://www.youtube.com/watch?list=abc"})

    assert response.status_code == 400
    assert "Invalid YouTube URL" in response.get_json()["error"]


# An unexpected AI/service error returns 500 with the error message.
def test_extract_unexpected_error_returns_500(client):
    with patch("src.api.extract_recipe.scrape_recipe", return_value=ScrapedPage("page", None)), \
         patch("src.api.extract_recipe.extract_recipe_from_text", side_effect=RuntimeError("OpenAI is down")):
        response = client.post("/recipes/extract", json={"url": "https://example.com/cake"})

    assert response.status_code == 500
    assert response.get_json()["error"] == "OpenAI is down"


# With no OPENAI_API_KEY configured, extraction returns 500 naming the missing key.
def test_extract_missing_api_key_returns_500(client):
    # The autouse fixture blanks the keys, so the real extractor fails on configuration
    with patch("src.api.extract_recipe.scrape_recipe", return_value=ScrapedPage("page", None)):
        response = client.post("/recipes/extract", json={"url": "https://example.com/cake"})

    assert response.status_code == 500
    assert "OPENAI_API_KEY" in response.get_json()["error"]


# ------------------------------------------------------------------ dish photo from the source

def _uploaded(app):
    import os
    folder = app.config["UPLOAD_FOLDER"]
    return os.listdir(folder) if os.path.isdir(folder) else []


def _web_recipe(image_url):
    model = RecipeExtracted(title="Pie", ingredients=["apples"], instructions=["bake"])
    return (patch("src.api.extract_recipe.scrape_recipe", return_value=ScrapedPage("text", image_url)),
            patch("src.api.extract_recipe.extract_recipe_from_text", return_value=model))


# When the page has an image, it is downloaded, stored and linked to the saved recipe.
def test_extract_saves_the_page_image(client, app, jpeg_bytes, monkeypatch):
    monkeypatch.setattr("src.services.recipe_image.download_image", lambda url: jpeg_bytes)
    scrape, extract = _web_recipe("https://cdn.example.com/pie.jpg")
    with scrape, extract:
        response = client.post("/recipes/extract", json={"url": "https://example.com/pie"})

    assert response.status_code == 201
    image_url = response.get_json()["image_url"]
    assert client.get(image_url).status_code == 200
    assert len(_uploaded(app)) == 1


# If the page has no image, or it can't be downloaded, the recipe is still saved (without a photo).
@pytest.mark.parametrize("image_url", [None, "https://cdn.example.com/broken.jpg"])
def test_extract_without_a_usable_image_still_saves_recipe(client, app, image_url):
    scrape, extract = _web_recipe(image_url)
    with scrape, extract:
        response = client.post("/recipes/extract", json={"url": "https://example.com/pie"})

    assert response.status_code == 201
    assert response.get_json()["image_url"] is None
    assert _uploaded(app) == []


# For a YouTube link the thumbnail is used: the best size is tried first, then the smaller one.
def test_extract_youtube_uses_thumbnail(client, jpeg_bytes, monkeypatch):
    tried = []

    def fake_download(url):
        tried.append(url)
        return jpeg_bytes if url.endswith("mqdefault.jpg") else None

    monkeypatch.setattr("src.services.recipe_image.download_image", fake_download)
    data = {"has_recipe": True, "title": "YT Salad", "ingredients": ["lettuce"], "instructions": ["toss"]}
    with patch("src.api.extract_recipe.extract_recipe_from_youtube", return_value=data):
        response = client.post("/recipes/extract", json={"url": "https://youtu.be/abc123"})

    assert response.status_code == 201
    assert response.get_json()["image_url"] is not None
    assert [u.split("/")[-1] for u in tried] == ["maxresdefault.jpg", "mqdefault.jpg"]
    assert "/vi/abc123/" in tried[0]


# A duplicate recipe is rejected before any photo is downloaded.
def test_extract_duplicate_does_not_download_image(client):
    client.post("/recipes", json={"title": "Pie", "ingredients": ["a"], "instructions": ["b"]})
    scrape, extract = _web_recipe("https://cdn.example.com/pie.jpg")
    with scrape, extract, patch("src.api.extract_recipe.fetch_and_store_image") as fetch:
        response = client.post("/recipes/extract", json={"url": "https://example.com/pie"})

    assert response.status_code == 409
    fetch.assert_not_called()


# If saving the recipe fails after the photo was stored, the photo file is removed again.
@pytest.mark.parametrize("error, status", [(RuntimeError("db down"), 500), (ValueError("bad row"), 400)])
def test_extract_failure_after_image_cleans_up_file(client, app, jpeg_bytes, monkeypatch, error, status):
    from src.core.database import db

    monkeypatch.setattr("src.services.recipe_image.download_image", lambda url: jpeg_bytes)
    scrape, extract = _web_recipe("https://cdn.example.com/pie.jpg")
    with scrape, extract, patch.object(db.session, "commit", side_effect=error):
        response = client.post("/recipes/extract", json={"url": "https://example.com/pie"})

    assert response.status_code == status
    assert _uploaded(app) == []
