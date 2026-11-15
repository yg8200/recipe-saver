import json
from unittest.mock import MagicMock, patch

import pytest

from src.services import facebook_extractor as fb

URL = "https://www.facebook.com/reel/123"


def ai_reply(**fields):
    base = {"title": None, "ingredients": [], "instructions": [], "prep_time": None, "cook_time": None, "servings": None}
    base.update(fields)
    msg = MagicMock()
    msg.choices[0].message.content = json.dumps(base, ensure_ascii=False)
    return msg


def fake_ydl(info=None, error=None):
    """A stand-in for yt_dlp.YoutubeDL that returns `info` (or raises `error`) and never touches the network."""
    ydl = MagicMock()
    ydl.__enter__.return_value = ydl
    ydl.extract_info.side_effect = error
    ydl.extract_info.return_value = info
    return ydl


# Real Facebook hosts are detected; lookalike domains and 'facebook.com' in the query are not.
@pytest.mark.parametrize("url, expected", [
    ("https://www.facebook.com/reel/123", True),
    ("https://facebook.com/watch/?v=1", True),
    ("https://m.facebook.com/story.php?id=1", True),
    ("https://fb.watch/abc/", True),
    ("https://notfacebook.com/reel/1", False),
    ("https://facebook.com.evil.com/reel/1", False),
    ("https://example.com/?ref=facebook.com", False),
    ("https://www.youtube.com/watch?v=abc", False),
])
def test_is_facebook_url(url, expected):
    assert fb.is_facebook_url(url) is expected


# The caption and the thumbnail are read from what yt-dlp returns.
def test_get_facebook_post_reads_caption_and_thumbnail():
    info = {"description": "the recipe", "thumbnail": "https://cdn.example.com/t.jpg", "title": "ignored"}
    with patch.object(fb.yt_dlp, "YoutubeDL", return_value=fake_ydl(info)):
        post = fb.get_facebook_post(URL)
    assert post.caption == "the recipe"
    assert post.thumbnail_url == "https://cdn.example.com/t.jpg"


# A post without a caption gives an empty caption instead of crashing.
def test_get_facebook_post_without_caption():
    with patch.object(fb.yt_dlp, "YoutubeDL", return_value=fake_ydl({"thumbnail": None})):
        post = fb.get_facebook_post(URL)
    assert post.caption == ""
    assert post.thumbnail_url is None


# When yt-dlp fails (private post, blocked), a clear ValueError is raised.
def test_get_facebook_post_failure_raises_clear_error():
    with patch.object(fb.yt_dlp, "YoutubeDL", return_value=fake_ydl(error=RuntimeError("login required"))):
        with pytest.raises(ValueError, match="private"):
            fb.get_facebook_post(URL)


# A caption with ingredients and steps becomes a recipe.
def test_caption_with_full_recipe_is_extracted():
    client = MagicMock()
    client.chat.completions.create.return_value = ai_reply(title="Pie", ingredients=["eggs"], instructions=["bake"])
    with patch.object(fb, "get_openai_client", return_value=client):
        result = fb.extract_recipe_from_facebook_caption("caption")
    assert result["title"] == "Pie"
    assert result["instructions"] == ["bake"]


# A caption without a complete recipe raises instead of saving a half recipe.
@pytest.mark.parametrize("reply", [
    ai_reply(),
    ai_reply(title="Pie", ingredients=["eggs"]),
    ai_reply(title="Pie", instructions=["bake"]),
])
def test_caption_without_complete_recipe_raises(reply):
    client = MagicMock()
    client.chat.completions.create.return_value = reply
    with patch.object(fb, "get_openai_client", return_value=client):
        with pytest.raises(ValueError, match="complete recipe"):
            fb.extract_recipe_from_facebook_caption("caption")


# An empty caption never calls the AI.
def test_empty_caption_does_not_call_ai():
    client = MagicMock()
    with patch.object(fb, "get_openai_client", return_value=client):
        with pytest.raises(ValueError):
            fb.extract_recipe_from_facebook_caption("   ")
    client.chat.completions.create.assert_not_called()
