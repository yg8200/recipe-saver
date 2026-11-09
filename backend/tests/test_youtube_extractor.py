import json
from unittest.mock import MagicMock, patch

import pytest

from src.services import youtube_extractor as yt

URL = "https://www.youtube.com/watch?v=abc123"


def ai_reply(**fields):
    base = {"title": None, "ingredients": [], "instructions": [], "prep_time": None, "cook_time": None, "servings": None}
    base.update(fields)
    msg = MagicMock()
    msg.choices[0].message.content = json.dumps(base, ensure_ascii=False)
    return msg


@pytest.fixture
def client():
    fake = MagicMock()
    with patch.object(yt, "get_openai_client", return_value=fake):
        yield fake


def run(client, description, ai_replies, transcript="spoken text", transcript_error=None):
    client.chat.completions.create.side_effect = ai_replies
    fetch = MagicMock(side_effect=transcript_error, return_value=transcript)
    with patch.object(yt, "get_video_description", return_value=description), \
         patch.object(yt, "get_video_transcript", fetch):
        return yt.extract_recipe_from_youtube(URL), fetch


# When the description has ingredients and instructions, it is used as-is and the transcript is never fetched.
def test_full_recipe_in_description_skips_transcript(client):
    result, fetch = run(client, "desc", [ai_reply(title="Cake", ingredients=["flour"], instructions=["bake"])])
    assert result["instructions"] == ["bake"]
    fetch.assert_not_called()
    assert client.chat.completions.create.call_count == 1


# When the description has only ingredients, the transcript fills in the instructions while the description's ingredients and title are kept.
def test_ingredients_only_uses_transcript_for_instructions(client):
    result, fetch = run(client, "desc", [
        ai_reply(title="Cake", ingredients=["200g flour", "2 eggs"], servings=8),
        ai_reply(title="Some Other Title", ingredients=["flour", "eggs"], instructions=["mix", "bake"]),
    ])
    fetch.assert_called_once_with("abc123")
    # Description ingredients/title are kept; instructions come from the transcript
    assert result["title"] == "Cake"
    assert result["ingredients"] == ["200g flour", "2 eggs"]
    assert result["instructions"] == ["mix", "bake"]
    assert result["servings"] == 8
    # The transcript prompt receives the description's partial recipe as context
    system_prompt = client.chat.completions.create.call_args_list[1].kwargs["messages"][0]["content"]
    assert "200g flour" in system_prompt


# When the description has no recipe, the whole recipe comes from the transcript (without partial-recipe context).
def test_no_recipe_in_description_uses_transcript(client):
    result, _ = run(client, "subscribe!", [
        ai_reply(),
        ai_reply(title="Soup", ingredients=["water"], instructions=["boil"]),
    ])
    assert result["title"] == "Soup"
    second_prompt = client.chat.completions.create.call_args_list[1].kwargs["messages"][0]["content"]
    assert "CONTEXT" not in second_prompt


# An empty description skips the AI call on it and goes straight to the transcript.
def test_empty_description_skips_first_ai_call(client):
    result, _ = run(client, "", [ai_reply(title="Soup", ingredients=["water"], instructions=["boil"])])
    assert result["title"] == "Soup"
    assert client.chat.completions.create.call_count == 1


# Ingredients-only description plus an unavailable transcript raises an error saying the instructions are missing.
def test_ingredients_only_and_no_transcript_raises_clear_error(client):
    with pytest.raises(ValueError, match="no instructions"):
        run(client, "desc", [ai_reply(title="Cake", ingredients=["flour"])],
            transcript_error=ValueError("disabled"))


# If even the transcript can't provide instructions, extraction fails instead of saving half a recipe.
def test_transcript_without_instructions_raises(client):
    with pytest.raises(ValueError, match="complete recipe"):
        run(client, "desc", [ai_reply(title="Cake", ingredients=["flour"]), ai_reply(ingredients=["flour"])])
