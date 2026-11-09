import json
from unittest.mock import MagicMock, patch

from src.services import recipe_corrector as rc

RECIPE = {
    "title": "באי תפוחים",
    "ingredients": ["4 תפוחים", "1/2 כוס סוכר"],
    "instructions": ["1. מחממים תנור", "3. שמים במקרה"],
    "prep_time": 10,
}


def test_apply_corrections_changes_only_listed_lines():
    result = rc.apply_corrections(RECIPE, [
        {"section": "title", "index": 0, "text": "פאי תפוחים"},
        {"section": "instructions", "index": 1, "text": "2. שמים במקרר"},
    ])
    assert result["title"] == "פאי תפוחים"
    assert result["instructions"] == ["1. מחממים תנור", "2. שמים במקרר"]
    assert result["ingredients"] == RECIPE["ingredients"]
    assert result["prep_time"] == 10
    assert RECIPE["title"] == "באי תפוחים"  # original not mutated


def test_apply_corrections_ignores_invalid_entries():
    result = rc.apply_corrections(RECIPE, [
        {"section": "ingredients", "index": 99, "text": "out of range"},
        {"section": "ingredients", "index": True, "text": "bool index"},
        {"section": "nope", "index": 0, "text": "bad section"},
        {"section": "ingredients", "index": 0, "text": "   "},
        "not a dict",
    ])
    assert result == RECIPE


def test_correct_recipe_text_with_no_corrections_returns_original():
    reply = MagicMock()
    reply.choices[0].message.content = json.dumps({"corrections": []})
    client = MagicMock()
    client.chat.completions.create.return_value = reply
    with patch.object(rc, "get_openai_client", return_value=client):
        result = rc.correct_recipe_text(RECIPE)
    # No AI changes; the broken "1., 3." numbering is fixed deterministically
    assert result == {**RECIPE, "instructions": ["1. מחממים תנור", "2. שמים במקרה"]}
    sent = json.loads(client.chat.completions.create.call_args.kwargs["messages"][1]["content"])
    assert sent["instructions"][1] == {"index": 1, "text": "3. שמים במקרה"}


def test_numbering_with_section_headers_is_left_alone():
    steps = ["--- מכינים את התפוחים ---", "1. a", "2. b", "--- שכבת השקדים ---", "3. c", "4. d"]
    assert rc.normalize_step_numbering(steps) == steps


def test_numbering_restarting_per_section_is_left_alone():
    steps = ["--- א ---", "1. a", "2. b", "--- ב ---", "1. c", "2. d"]
    assert rc.normalize_step_numbering(steps) == steps


def test_broken_numbering_is_renumbered():
    steps = ["1. a", "3. b", "--- header ---", "3) c", "unnumbered note"]
    assert rc.normalize_step_numbering(steps) == ["1. a", "2. b", "--- header ---", "3. c", "unnumbered note"]


def test_unnumbered_steps_are_untouched():
    steps = ["mix", "bake"]
    assert rc.normalize_step_numbering(steps) == steps
