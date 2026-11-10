import json
from unittest.mock import MagicMock, patch

import pytest

from src.services import recipe_corrector as rc

RECIPE = {
    "title": "באי תפוחים",
    "ingredients": ["4 תפוחים", "1/2 כוס סוכר"],
    "instructions": ["1. מחממים תנור", "3. שמים במקרה"],
    "prep_time": 10,
}


def fix(section, index, original, text):
    return {"section": section, "index": index, "original": original, "text": text}


def reply_with(content: dict):
    reply = MagicMock()
    reply.choices[0].message.content = json.dumps(content)
    client = MagicMock()
    client.chat.completions.create.return_value = reply
    return client


# Corrections replace only the lines they point to and never mutate the original recipe.
def test_apply_corrections_changes_only_listed_lines():
    result = rc.apply_corrections(RECIPE, [
        fix("title", 0, "באי תפוחים", "פאי תפוחים"),
        fix("instructions", 1, "3. שמים במקרה", "3. שמים במקרר"),
    ])
    assert result["title"] == "פאי תפוחים"
    assert result["instructions"] == ["1. מחממים תנור", "3. שמים במקרר"]
    assert result["ingredients"] == RECIPE["ingredients"]
    assert result["prep_time"] == 10
    assert RECIPE["title"] == "באי תפוחים"  # original not mutated


# Corrections with bad indexes, unknown sections, empty text, wrong types or no quoted original are ignored.
def test_apply_corrections_ignores_invalid_entries():
    result = rc.apply_corrections(RECIPE, [
        fix("ingredients", 99, "x", "out of range"),
        fix("ingredients", True, "4 תפוחים", "bool index"),
        fix("nope", 0, "x", "bad section"),
        fix("ingredients", 0, "4 תפוחים", "   "),
        {"section": "ingredients", "index": 0, "text": "4 תפוחים"},  # no "original" quoted
        "not a dict",
    ])
    assert result == RECIPE
    assert rc.apply_corrections(RECIPE, "not a list") == RECIPE


# A correction whose quoted original is not the line at that index (the model lost its place) is skipped.
def test_apply_corrections_skips_when_quoted_original_does_not_match():
    result = rc.apply_corrections(RECIPE, [fix("ingredients", 1, "4 תפוחים", "1/2 כוס סוכר")])
    assert result == RECIPE


# Fixing a misread letter is accepted, including words split or merged by OCR.
@pytest.mark.parametrize("original, corrected", [
    ("1 כוס מים פושדים", "1 כוס מים פושרים"),
    ("מלה", "מלח"),                       # one-word line
    ("מערבבים מיץלימון", "מערבבים מיץ לימון"),   # words merged by OCR
])
def test_review_accepts_typo_fixes(original, corrected):
    assert rc.review_correction(original, corrected) is None


# Anything that adds, removes or rewrites words, or touches numbers or headers, is rejected.
@pytest.mark.parametrize("original, corrected, reason", [
    ("פפריקה חריפה", "1 כפית פפריקה חריפה", "numbers changed"),               # invented a quantity
    ("סלט טחינה", "סלט טחינה גולמית", "words were added or removed"),          # added a word
    ("בצק פיצה ביתי", "בצק פיצה", "words were added or removed"),              # dropped a word
    ("כמה שצריך מים", "מים לפי הצורך", "too many words changed"),   # rewrote it
    ("מוסיפים קצת מלח ומערבבים", "מוסיפים מלח ומערבבים היטב", "too many words changed"),  # shifted words
    ("3 כוסות קמח", "5 כוסות קמח", "numbers changed"),
    ("--- למילוי ---", "--- למלית ---", "section header"),
    ("מלח", "מלח", "no change"),
    ("מוסיפים סוכר", "מוסיפים בצל", "a word was replaced by a different word"),  # a different ingredient
    ("a b c d e f", "x y z d e f", "too many words changed"),
])
def test_review_rejects_rewrites(original, corrected, reason):
    assert rc.review_correction(original, corrected) == reason


# A rewrite proposed by the model is dropped by apply_corrections and the original line is kept.
def test_apply_corrections_drops_rewrites():
    recipe = {"title": "סלט טחינה", "ingredients": ["פפריקה חריפה"], "instructions": ["1. מערבבים"]}
    result = rc.apply_corrections(recipe, [
        fix("title", 0, "סלט טחינה", "סלט טחינה גולמית"),
        fix("ingredients", 0, "פפריקה חריפה", "1 כפית פפריקה חריפה"),
    ])
    assert result == recipe


# A dish title is never replaced; a title the model says is not a dish name is replaced by a short, number-free one.
def test_title_replacement_only_when_not_a_dish_name():
    recipe = {"title": "אתר המתכונים של דנה", "ingredients": ["a"], "instructions": ["b"]}
    assert rc.apply_corrections(recipe, [], True, "פשטידה")["title"] == "אתר המתכונים של דנה"
    assert rc.apply_corrections(recipe, [], False, " תפוחי אדמה  אפויים ")["title"] == "תפוחי אדמה אפויים"
    # Unusable replacements (empty, too long, with digits, wrong type) leave the title alone
    for bad in (None, "", "   ", "אחת שתיים שלוש ארבע חמש שש", "מנה 5", 7):
        assert rc.apply_corrections(recipe, [], False, bad)["title"] == "אתר המתכונים של דנה"


# With no AI corrections the recipe is unchanged (except deterministic renumbering), and lines are sent to the AI with indexes.
def test_correct_recipe_text_with_no_corrections_returns_original():
    client = reply_with({"corrections": []})
    with patch.object(rc, "get_openai_client", return_value=client):
        result = rc.correct_recipe_text(RECIPE)
    # No AI changes; the broken "1., 3." numbering is fixed deterministically
    assert result == {**RECIPE, "instructions": ["1. מחממים תנור", "2. שמים במקרה"]}
    sent = json.loads(client.chat.completions.create.call_args.kwargs["messages"][1]["content"])
    assert sent["instructions"][1] == {"index": 1, "text": "3. שמים במקרה"}


# The corrector uses gpt-4o unless a model is configured, and the title is sent along for checking.
def test_correct_recipe_text_uses_gpt4o_by_default_and_sends_title(monkeypatch):
    for var in ("OPENAI_CORRECTOR_MODEL", "AI_MODEL_NAME"):
        monkeypatch.delenv(var, raising=False)
    client = reply_with({"corrections": []})
    with patch.object(rc, "get_openai_client", return_value=client):
        rc.correct_recipe_text(RECIPE)
    call = client.chat.completions.create.call_args.kwargs
    assert call["model"] == "gpt-4o"
    assert json.loads(call["messages"][1]["content"])["title"] == "באי תפוחים"


# Valid fixes from the model are applied; a rewrite in the same reply is rejected.
def test_correct_recipe_text_applies_valid_fixes_and_rejects_rewrites():
    client = reply_with({"title_is_dish_name": True, "corrections": [
        fix("title", 0, "באי תפוחים", "פאי תפוחים"),
        fix("ingredients", 1, "1/2 כוס סוכר", "1/2 כוס סוכר לבן"),
    ]})
    with patch.object(rc, "get_openai_client", return_value=client):
        result = rc.correct_recipe_text(RECIPE)
    assert result["title"] == "פאי תפוחים"
    assert result["ingredients"] == RECIPE["ingredients"]


# A model reply that is not a JSON object is an error (the upload route then falls back to the raw OCR text).
def test_correct_recipe_text_rejects_non_object_reply():
    client = reply_with(["not", "an", "object"])
    with patch.object(rc, "get_openai_client", return_value=client), pytest.raises(ValueError):
        rc.correct_recipe_text(RECIPE)


# Steps numbered 1..n across section headers are already correct and must not be renumbered.
def test_numbering_with_section_headers_is_left_alone():
    steps = ["--- מכינים את התפוחים ---", "1. a", "2. b", "--- שכבת השקדים ---", "3. c", "4. d"]
    assert rc.normalize_step_numbering(steps) == steps


# Steps that restart at 1 in each section are valid and must not be renumbered.
def test_numbering_restarting_per_section_is_left_alone():
    steps = ["--- א ---", "1. a", "2. b", "--- ב ---", "1. c", "2. d"]
    assert rc.normalize_step_numbering(steps) == steps


# Skipped or duplicate step numbers are renumbered 1..n, leaving headers and unnumbered lines alone.
def test_broken_numbering_is_renumbered():
    steps = ["1. a", "3. b", "--- header ---", "3) c", "unnumbered note"]
    assert rc.normalize_step_numbering(steps) == ["1. a", "2. b", "--- header ---", "3. c", "unnumbered note"]


# Instructions without step numbers are returned unchanged.
def test_unnumbered_steps_are_untouched():
    steps = ["mix", "bake"]
    assert rc.normalize_step_numbering(steps) == steps
