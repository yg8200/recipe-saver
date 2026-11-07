import base64
import json
import os
import io
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import pillow_heif

# Register HEIF opener so Pillow can open .heic files
pillow_heif.register_heif_opener()

load_dotenv()

def get_openai_client() -> OpenAI:
    """
    Retrieves the OpenAI client with the validated API key from the environment.
    """
    api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("AI_BASE_URL") 
    
    if not api_key:
        raise ValueError("AI_API_KEY or OPENAI_API_KEY is not set.")
        
    return OpenAI(api_key=api_key, base_url=base_url)


def extract_recipe_from_image(image_bytes: bytes, mime_type: str) -> dict:
    """
    Encodes image bytes and extracts structured recipe data using a vision LLM.
    Converts HEIC to JPEG automatically.
    """
    if "heic" in mime_type.lower() or "heif" in mime_type.lower():
        image = Image.open(io.BytesIO(image_bytes))
        jpeg_buffer = io.BytesIO()
        image.convert("RGB").save(jpeg_buffer, format="JPEG")
        image_bytes = jpeg_buffer.getvalue()
        mime_type = "image/jpeg"

    client = get_openai_client()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    # Strictly English prompt enforcing mechanical OCR behavior
    system_prompt = """
    You are a mechanical OCR (Optical Character Recognition) engine. You have no culinary knowledge.
    Your ONLY purpose is to transcribe Hebrew text from an image into a JSON format exactly word-for-word.

    CRITICAL OCR RULES:
    1. ZERO HALLUCINATION: Do NOT add, guess, or invent any ingredients, instructions, spices, or times. If a word or number is not explicitly visible in the image, it does not exist.
    2. INGREDIENTS LIST: Locate the ingredients column. Copy every single line exactly as printed, including all numbers, fractions, units, and parentheses (e.g., "4 תפוחים (לא משנה מאיזה סוג)"). Do not drop numbers.
    3. INSTRUCTIONS LIST: Locate the numbered paragraphs (1, 2, 3...) in the center of the page. Transcribe every step in full, exactly word-for-word.
    4. SUB-SECTIONS: If you see bold text or dividers (e.g., "לשכבת התפוחים ולזיגוג:", "מכינים את התפוחים"), add them as standalone items in the list wrapped in dashes: "--- לשכבת התפוחים ולזיגוג ---".
    5. NULL FIELDS: If prep_time, cook_time, or servings are not explicitly written as numbers in the image, you MUST return null.
    6. ORIGINAL LANGUAGE: Keep all extracted text in Hebrew. Do not translate anything to English.
    7. If you see a title for any sub-section then keep all the text under that sub-section until the next sub-section or the end of the list.
    8. dont invent anything. make sure that only the text that is visible in the image is included in the output. If you see a number or a word, include it. If you don't see it, do not include it.

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

    target_model = os.getenv("AI_MODEL_NAME", "gpt-4o")

    response = client.chat.completions.create(
        model=target_model,
        temperature=0.0,  # Enforce strict determinism
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Perform a strict OCR scan on this image and output the JSON."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}",
                            "detail": "high"  # Crucial for reading dense Hebrew text
                        }
                    }
                ]
            }
        ]
    )

    extracted_json = response.choices[0].message.content
    return json.loads(extracted_json)