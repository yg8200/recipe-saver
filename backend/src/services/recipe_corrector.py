import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)

def correct_recipe_text(recipe_json: dict) -> dict:
    """
    Acts as an AI guardrail/editor to fix Hebrew OCR typos and formatting issues.
    """
    client = get_openai_client()
    
    system_prompt = """
    You are an expert culinary editor, highly fluent in Hebrew.
    You will receive a JSON of a Hebrew recipe extracted by an OCR engine.
    Due to OCR limitations, the text contains visual typos (e.g., 'באי' instead of 'פאי', 'במקרה' instead of 'במקרר', 'מגרענים' instead of 'מסירים') and inconsistent numbering in the instructions.
    
    CRITICAL RULES:
    1. Fix all visual OCR typos and broken verbs based on culinary context.
    2. Fix and organize the numbering of the instructions so they are clean, sequential, and consistent.
    3. DO NOT add ingredients or steps that were not in the original text. Do not invent a new recipe.
    4. Keep the exact same JSON structure.
    5. Validate the Hebrew sntax so numbers, units, and culinary terms are correct and well ordered.
    
    Return ONLY a valid JSON object with the corrected Hebrew text.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0, 
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(recipe_json, ensure_ascii=False)}
        ]
    )
    
    return json.loads(response.choices[0].message.content)