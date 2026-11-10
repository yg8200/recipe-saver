import copy
import json
import logging
import re

from src.services.ai_client import get_openai_client, get_openai_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You proofread Hebrew recipes that an OCR engine read from a photo. You receive JSON where every line
has an index. Your ONLY job is to fix words the OCR MISREAD. You are a proofreader, not an editor.

WHAT COUNTS AS AN OCR ERROR
A word that is not a real Hebrew word, or makes no sense in a cooking context, because the OCR confused
visually similar letters (ר/ד, ח/ה/ת, ם/ס, ו/ז/ן, ב/כ, ג/נ, י/ו, ל/ו...).
Read EVERY word of EVERY line and ask: "is this a real word that fits here?". If not, fix it.

HARD RULES
1. Change a line only to fix a misread word. Never add, remove, reorder or rephrase words.
2. Never add quantities, ingredients, explanations or missing details. Never change any number.
3. Do NOT fix grammar, style, punctuation, spelling variants, or casual / vague wording
   ("קצת מלח", "לפי הטעם", "עד שמוכן"). If a line is understandable and uses real words, leave it EXACTLY as is.
4. When you are not sure a word is an OCR error, do not change it.
5. Leave section header lines (like "--- למילוי ---") alone.

EXAMPLES
 "מוסיפים מלה ופלפל"       -> "מוסיפים מלח ופלפל"      (ח was read as ה)
 "מכסים בנייד אלומיניום"   -> "מכסים בנייר אלומיניום"   (ר was read as ד)
 "1 כוס סוכד"              -> "1 כוס סוכר"              (the number stays)
 "קוצצים בצל דק"           -> unchanged                  (already correct)
 "מבשלים קצת עד שמסמיך"    -> unchanged                  (casual wording, not an error; do not add anything)
 "1/2 כוס שמן זית"         -> unchanged                  (never touch numbers)

THE TITLE
The title must be the name of a dish.
- If it is a dish name, leave it unless it has a misread word. Never shorten, extend or rephrase it.
  A misread word in the title is fixed with a normal correction (section "title").
- If it is clearly NOT a dish name (a website, magazine or author name, a section header, a slogan,
  a date), set "title_is_dish_name" to false and give "replacement_title": a short dish name
  (at most 5 words) based on the ingredients and steps.

OUTPUT
Return ONLY this JSON object. Each correction repeats the line exactly as you received it in
"original", and gives the full corrected line in "text". If nothing needs fixing, "corrections" is [].
{
    "title_is_dish_name": true,
    "replacement_title": null,
    "corrections": [
        {"section": "title" | "ingredients" | "instructions", "index": 0, "original": "line as received", "text": "full corrected line"}
    ]
}
For "title", use index 0.
"""

DEFAULT_CORRECTOR_MODEL = "gpt-4o"
SECTIONS = ("ingredients", "instructions")
STEP_NUMBER = re.compile(r"^\s*(\d+)\s*[.)]\s*")
SECTION_HEADER = re.compile(r"^\s*-{2,}")  # lines like "--- למילוי ---"
NUMBER = re.compile(r"\d+")
MAX_REPLACEMENT_TITLE_WORDS = 5

# A real OCR fix changes the letters of a word or two. These limits are what separates that from a rewrite.
MIN_WORD_SIMILARITY = 0.5   # a changed word must still look like the original word
MIN_SPLIT_MERGE_SIMILARITY = 0.9  # when a word is split or merged ("מיץלימון" -> "מיץ לימון")


def _indexed_view(recipe: dict) -> dict:
    """Numbers every line so the model can point at the lines it changes."""
    view = {"title": recipe.get("title")}
    for section in SECTIONS:
        lines = recipe.get(section)
        view[section] = [{"index": i, "text": line} for i, line in enumerate(lines)] if isinstance(lines, list) else []
    return view


def _similarity(a: str, b: str) -> float:
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()


def review_correction(original: str, corrected: str) -> str | None:
    """Deterministic check that a proposed change is a typo fix and not a rewrite.

    Returns None when the change is acceptable, otherwise a short reason for rejecting it.
    We do not trust the model to follow "only fix typos" on its own, so every change must also pass this.
    """
    if corrected == original:
        return "no change"
    if SECTION_HEADER.match(original):
        return "section header"
    if NUMBER.findall(original) != NUMBER.findall(corrected):
        return "numbers changed"

    old_words, new_words = original.split(), corrected.split()
    if len(old_words) == len(new_words):
        changed = [(o, n) for o, n in zip(old_words, new_words) if o != n]
        if len(changed) > max(2, len(old_words) // 3):
            return "too many words changed"
        if any(_similarity(o, n) < MIN_WORD_SIMILARITY for o, n in changed):
            return "a word was replaced by a different word"
        return None
    if abs(len(old_words) - len(new_words)) == 1 and _similarity(original, corrected) >= MIN_SPLIT_MERGE_SIMILARITY:
        return None  # a word was split or two words were merged
    return "words were added or removed"


def _clean_replacement_title(value) -> str | None:
    if not isinstance(value, str):
        return None
    title = " ".join(value.split())
    if not title or len(title.split()) > MAX_REPLACEMENT_TITLE_WORDS or NUMBER.search(title):
        return None
    return title


def apply_corrections(recipe: dict, corrections, title_is_dish_name=True, replacement_title=None) -> dict:
    """Applies the model's corrections, keeping only the ones that pass review.

    A correction is skipped when it points at a line that doesn't exist, when the "original" it quotes
    is not the line at that index (the model lost its place), or when review_correction rejects it.
    """
    corrected = copy.deepcopy(recipe)

    if isinstance(corrections, list):
        for fix in corrections:
            if not isinstance(fix, dict):
                continue
            section, index, text, quoted = fix.get("section"), fix.get("index"), fix.get("text"), fix.get("original")
            if not isinstance(text, str) or not text.strip() or not isinstance(index, int) or isinstance(index, bool):
                continue
            text = text.strip()

            if section == "title" and index == 0 and isinstance(corrected.get("title"), str):
                holder, key = corrected, "title"
            elif section in SECTIONS and isinstance(corrected.get(section), list) and 0 <= index < len(corrected[section]):
                holder, key = corrected[section], index
            else:
                continue

            current = holder[key]
            if not isinstance(current, str) or not isinstance(quoted, str) or quoted.strip() != current.strip():
                logger.info("Corrector change skipped (it quoted a different line): %r", fix)
                continue
            reason = review_correction(current, text)
            if reason:
                logger.info("Corrector change rejected (%s): %r -> %r", reason, current, text)
                continue
            holder[key] = text

    # Replacing the whole title is only allowed when the model says it is not a dish name
    if title_is_dish_name is False:
        new_title = _clean_replacement_title(replacement_title)
        if new_title:
            corrected["title"] = new_title

    return corrected


def _is_sequential(numbers: list[int]) -> bool:
    return numbers == list(range(1, len(numbers) + 1))


def normalize_step_numbering(instructions: list) -> list:
    """
    Deterministically fixes step numbering. Lines without a leading number (section headers)
    are not steps. Numbering is left alone if it already runs 1..n overall, or restarts at 1
    in each section; otherwise numbered steps are renumbered 1..n in order.
    """
    if not isinstance(instructions, list):
        return instructions

    sections, current = [], []
    for line in instructions:
        match = STEP_NUMBER.match(line) if isinstance(line, str) else None
        if match:
            current.append(int(match.group(1)))
        elif current:
            sections.append(current)
            current = []
    if current:
        sections.append(current)

    all_numbers = [n for section in sections for n in section]
    if not all_numbers or _is_sequential(all_numbers) or all(_is_sequential(sec) for sec in sections):
        return instructions

    result, step = [], 0
    for line in instructions:
        if isinstance(line, str) and STEP_NUMBER.match(line):
            step += 1
            line = STEP_NUMBER.sub(f"{step}. ", line, count=1)
        result.append(line)
    return result


def correct_recipe_text(recipe_json: dict) -> dict:
    """
    AI guardrail that fixes words the OCR misread, and nothing else.

    Two layers keep it from "thinking too much": the prompt limits the model to fixing misread words,
    and review_correction() then rejects any change that adds, removes or rewrites words or touches
    numbers. The model returns only the lines it changed, so a clean OCR result costs few output tokens.
    """
    client = get_openai_client()
    response = client.chat.completions.create(
        # gpt-4o-mini misses subtle Hebrew typos and misjudges others; gpt-4o is not slower here and the
        # input is only a few hundred tokens, so the extra cost is a fraction of a cent (see evals/).
        model=get_openai_model("OPENAI_CORRECTOR_MODEL", default=DEFAULT_CORRECTOR_MODEL),
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(_indexed_view(recipe_json), ensure_ascii=False)},
        ],
    )
    result = json.loads(response.choices[0].message.content)
    if not isinstance(result, dict):
        raise ValueError("Corrector did not return a JSON object")
    corrected = apply_corrections(
        recipe_json,
        result.get("corrections"),
        title_is_dish_name=result.get("title_is_dish_name", True),
        replacement_title=result.get("replacement_title"),
    )
    corrected["instructions"] = normalize_step_numbering(corrected.get("instructions"))
    return corrected
