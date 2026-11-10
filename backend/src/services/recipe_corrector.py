import copy
import json
import re

from src.services.ai_client import get_openai_client, get_openai_model

SYSTEM_PROMPT = """
You are an expert culinary editor, highly fluent in Hebrew.
You will receive a JSON of a Hebrew recipe extracted by an OCR engine. Every line has an index.
The text may contain visual OCR typos (e.g., 'באי' instead of 'פאי', 'במקרה' instead of 'במקרר',
'מגרענים' instead of 'מסירים') 

CRITICAL RULES:
1. Fix visual OCR typos and broken verbs based on culinary context.
2. Validate the Hebrew syntax so numbers, units and culinary terms are correct and well ordered.
3. ALWAYS CHECK THE TITLE (section "title"). It must be the name of the dish. Fix OCR typos in it.
   If it is clearly NOT a dish name (e.g. a website or magazine name, a section header, a slogan,
   an author, a date, a page number), replace it with a short, accurate dish name based on the
   ingredients and steps. If the title already fits the recipe, leave it unchanged.
4. DO NOT add or remove lines, ingredients or steps. Do not invent a new recipe.
5. DO NOT change step numbers (e.g. "4.") - numbering is handled separately.
6. Only fix real errors. Do not make stylistic or punctuation-only changes (e.g., do not add periods),
   and leave section header lines (such as "--- לשכבת השקדים ---" or "מכינים את התפוחים") unchanged.
7. Return ONLY the lines you changed. Never return a line identical to the original.
   If nothing needs fixing, return an empty list.

Return ONLY a valid JSON object with this structure:
{
    "corrections": [
        {"section": "title" | "ingredients" | "instructions", "index": 0, "text": "the full corrected line"}
    ]
}
For "title", use index 0.
"""

SECTIONS = ("ingredients", "instructions")
STEP_NUMBER = re.compile(r"^\s*(\d+)\s*[.)]\s*")


def _indexed_view(recipe: dict) -> dict:
    """Numbers every line so the model can point at the lines it changes."""
    view = {"title": recipe.get("title")}
    for section in SECTIONS:
        lines = recipe.get(section)
        view[section] = [{"index": i, "text": line} for i, line in enumerate(lines)] if isinstance(lines, list) else []
    return view


def apply_corrections(recipe: dict, corrections) -> dict:
    """Applies line-level corrections, ignoring any that point at lines that do not exist."""
    corrected = copy.deepcopy(recipe)
    if not isinstance(corrections, list):
        return corrected
    for fix in corrections:
        if not isinstance(fix, dict):
            continue
        section, index, text = fix.get("section"), fix.get("index"), fix.get("text")
        if not isinstance(text, str) or not text.strip() or not isinstance(index, int) or isinstance(index, bool):
            continue
        if section == "title":
            corrected["title"] = text.strip()
        elif section in SECTIONS and isinstance(corrected.get(section), list) and 0 <= index < len(corrected[section]):
            corrected[section][index] = text.strip()
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
    AI guardrail/editor that fixes Hebrew OCR typos and formatting issues.
    The model returns only the lines it changed, so a clean OCR result costs very few output tokens.
    """
    client = get_openai_client()
    response = client.chat.completions.create(
        model=get_openai_model("OPENAI_CORRECTOR_MODEL"),
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
    corrected = apply_corrections(recipe_json, result.get("corrections"))
    corrected["instructions"] = normalize_step_numbering(corrected.get("instructions"))
    return corrected
