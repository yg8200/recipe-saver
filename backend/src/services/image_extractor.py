import json
import os
import io
from dotenv import load_dotenv
from PIL import Image
import pillow_heif
from google import genai
from google.genai import types

# Register HEIF opener so Pillow can open .heic files from iPhones
pillow_heif.register_heif_opener()

load_dotenv()

def get_gemini_client() -> genai.Client:
    """Initializes the official Google GenAI client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in your .env file.")
    return genai.Client(api_key=api_key)

def extract_recipe_from_image(image_bytes: bytes, mime_type: str) -> dict:
    """
    Extracts structured recipe data using Gemini 2.5 Flash, 
    which has superior native Hebrew OCR capabilities.
    """
    # Convert HEIC to JPEG if necessary
    if "heic" in mime_type.lower() or "heif" in mime_type.lower():
        image = Image.open(io.BytesIO(image_bytes))
        jpeg_buffer = io.BytesIO()
        image.convert("RGB").save(jpeg_buffer, format="JPEG")
        image_bytes = jpeg_buffer.getvalue()
    
    # Load the final image into memory for Gemini
    pil_image = Image.open(io.BytesIO(image_bytes))
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

    # Call Gemini 2.5 Flash with strict JSON formatting and zero temperature
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=[system_prompt, pil_image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )

    return json.loads(response.text)