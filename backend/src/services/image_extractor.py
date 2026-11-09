import json
import io
from PIL import Image
from google.genai import types

from src.utils.image_processing import process_and_compress_image
from src.services.ai_client import get_gemini_client, get_gemini_model, get_gemini_thinking_config


def extract_recipe_from_image(image_bytes: bytes, mime_type: str) -> dict:
    # 1. Pass the raw bytes to your new compression module
    # We no longer need the mime_type check because the module forces everything to JPEG
    optimized_image_bytes = process_and_compress_image(image_bytes)
    
    # 2. Load the optimized image for Gemini
    pil_image = Image.open(io.BytesIO(optimized_image_bytes))
    client = get_gemini_client()
    
    system_prompt = """
    You are a mechanical OCR engine. Your ONLY purpose is to transcribe Hebrew text from a recipe image into JSON exactly word-for-word.

    CRITICAL OCR RULES:
    1. IGNORE NOISE: Completely ignore any handwritten notes (e.g., text written in pen) and ignore any long introductory paragraphs.
    2. INGREDIENTS: Look ONLY at the ingredients section (usually a side column). Copy the ingredients exactly as printed, including formatting lines like "--- לשכבת התפוחים ולזיגוג ---".
    3. INSTRUCTIONS: Look ONLY at the numbered list of instructions. Copy every step word-for-word exactly as it appears.
    4. ZERO HALLUCINATION: Do not add, guess, or invent any ingredients, instructions, or spices. If a word or number is not explicitly printed in the main text, it does not exist.
    5. NULL FIELDS: If prep_time, cook_time, or servings are not explicitly written as numbers, you MUST return null.
    6. ORIGINAL LANGUAGE: Keep all extracted text in Hebrew. Do not translate anything.

    Return ONLY a valid JSON object matching this exact structure:
    {
        "title": "Exact title copied from image",
        "ingredients": ["--- section header ---", "exact line 1", "exact line 2"],
        "instructions": ["--- section header ---", "exact step 1", "exact step 2"],
        "prep_time": null,
        "cook_time": null,
        "servings": null
    }
    """

    model = get_gemini_model()
    response = client.models.generate_content(
        model=model,
        contents=[system_prompt, pil_image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
            thinking_config=get_gemini_thinking_config(model),
        ),
    )

    return json.loads(response.text)