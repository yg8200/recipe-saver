from unittest.mock import patch

import pytest

from src.api.extract_recipe import validate_extracted_recipe
from src.schemas.recipe_schema import RecipeExtracted
from src.services.youtube_extractor import get_youtube_video_id, is_youtube_url


def test_validate_accepts_pydantic_model_from_url_extractor():
    model = RecipeExtracted(
        title="  Pancakes ", ingredients=["flour"], instructions=["mix"], prep_time_minutes=5
    )
    result = validate_extracted_recipe(model)
    assert result["title"] == "Pancakes"
    assert result["prep_time_minutes"] == 5


def test_validate_accepts_short_time_keys_and_drops_bad_numbers():
    result = validate_extracted_recipe({
        "title": "Soup", "ingredients": ["water", " ", None], "instructions": ["boil"],
        "prep_time": 10, "cook_time": True, "servings": -2,
    })
    assert result["ingredients"] == ["water"]
    assert result["prep_time_minutes"] == 10
    assert result["cook_time_minutes"] is None
    assert result["servings"] is None


def test_validate_rejects_whitespace_only_ingredients():
    with pytest.raises(ValueError):
        validate_extracted_recipe({"title": "x", "ingredients": ["  "], "instructions": ["a"]})


@pytest.mark.parametrize("url, expected", [
    ("https://www.youtube.com/watch?v=abc123&t=10", "abc123"),
    ("https://youtu.be/abc123?si=xyz", "abc123"),
    ("https://youtube.com/shorts/abc123", "abc123"),
    ("https://m.youtube.com/embed/abc123", "abc123"),
])
def test_get_youtube_video_id(url, expected):
    assert get_youtube_video_id(url) == expected


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?list=abc", "https://www.youtube.com/", "https://youtu.be/",
])
def test_get_youtube_video_id_invalid(url):
    with pytest.raises(ValueError):
        get_youtube_video_id(url)


def test_is_youtube_url_does_not_match_lookalike_domains():
    assert is_youtube_url("https://youtu.be/abc")
    assert not is_youtube_url("https://notyoutube.com/watch?v=abc")
    assert not is_youtube_url("https://example.com/?ref=youtube.com")


def test_extract_from_webpage_saves_recipe(client):
    model = RecipeExtracted(title="Web Cake", ingredients=["sugar"], instructions=["bake"], cook_time_minutes=30)
    with patch("src.api.extract_recipe.scrape_recipe_page", return_value="page text"), \
         patch("src.api.extract_recipe.extract_recipe_from_text", return_value=model):
        response = client.post("/recipes/extract", json={"url": "https://example.com/cake"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Web Cake"
    assert body["cook_time_minutes"] == 30


def test_extract_routes_youtube_urls(client):
    data = {"has_recipe": True, "title": "YT Salad", "ingredients": ["lettuce"], "instructions": ["toss"]}
    with patch("src.api.extract_recipe.extract_recipe_from_youtube", return_value=data) as yt, \
         patch("src.api.extract_recipe.scrape_recipe_page") as scraper:
        response = client.post("/recipes/extract", json={"url": "https://youtu.be/abc"})
    assert response.status_code == 201
    yt.assert_called_once()
    scraper.assert_not_called()


@pytest.mark.parametrize("kwargs", [{"data": "not json"}, {"json": ["a list"]}, {"json": {"url": ""}}])
def test_extract_rejects_bad_body(client, kwargs):
    response = client.post("/recipes/extract", **kwargs)
    assert response.status_code == 400
