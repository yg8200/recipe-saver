from flask import Blueprint, jsonify, request
from pydantic import BaseModel
from sqlalchemy import func
from src.core.database import db
from src.models.recipe import Recipe

# Ensure these imports match your actual file names
from src.services.scraper import scrape_recipe
from src.services.image_store import delete_recipe_image
from src.services.recipe_image import fetch_and_store_image, youtube_thumbnail_urls
from src.services.ai_extractor import extract_recipe_from_text
from src.services.youtube_extractor import extract_recipe_from_youtube, get_youtube_video_id, is_youtube_url

extract_recipe_bp = Blueprint("extract_recipe", __name__)

def _optional_non_negative_int(data: dict, *keys: str) -> int | None:
    """Returns the first non-negative int found under any of the given keys, else None."""
    for key in keys:
        value = data.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    return None


def validate_extracted_recipe(data) -> dict:
    """Validates and cleans the AI extracted recipe data."""
    # The URL extractor returns a Pydantic model; the image/YouTube extractors return dicts.
    if isinstance(data, BaseModel):
        data = data.model_dump()

    if not isinstance(data, dict):
        raise ValueError("AI did not return a valid JSON object.")

    title = data.get("title")
    if not title or not isinstance(title, str) or title.strip() == "":
        raise ValueError("Extraction failed: Could not find a valid recipe title.")

    ingredients = data.get("ingredients")
    if not isinstance(ingredients, list):
        raise ValueError("Extraction failed: No ingredients were found in this source.")
    ingredients = [str(i).strip() for i in ingredients if i is not None and str(i).strip()]
    if not ingredients:
        raise ValueError("Extraction failed: No ingredients were found in this source.")

    instructions = data.get("instructions")
    if not isinstance(instructions, list):
        raise ValueError("Extraction failed: No instructions were found in this source.")
    instructions = [str(i).strip() for i in instructions if i is not None and str(i).strip()]
    if not instructions:
        raise ValueError("Extraction failed: No instructions were found in this source.")

    # Extractors use either "prep_time" or "prep_time_minutes" naming; accept both.
    return {
        "title": title.strip()[:255],
        "ingredients": ingredients,
        "instructions": instructions,
        "prep_time_minutes": _optional_non_negative_int(data, "prep_time_minutes", "prep_time"),
        "cook_time_minutes": _optional_non_negative_int(data, "cook_time_minutes", "cook_time"),
        "servings": _optional_non_negative_int(data, "servings"),
    }


@extract_recipe_bp.post("/recipes/extract")
def extract_recipe():
    data = request.get_json(silent=True)
    url = data.get("url") if isinstance(data, dict) else None

    if not isinstance(url, str) or not url.strip():
        return jsonify({"error": "The 'url' field is required in the JSON body"}), 400

    url = url.strip()
    image_filename = None  # set once a photo is stored; cleaned up again if saving the recipe fails

    try:
        # Route to the correct extraction service
        if is_youtube_url(url):
            # The YouTube extractor now handles description vs transcript logic internally
            raw_extracted = extract_recipe_from_youtube(url)
            image_candidates = youtube_thumbnail_urls(get_youtube_video_id(url))
        else:
            # Standard webpage scraping: one fetch gives both the text and the page's main image
            page = scrape_recipe(url)
            raw_extracted = extract_recipe_from_text(page.text)
            image_candidates = [page.image_url]

        # Apply the guardrail to ensure the AI actually found valid lists
        validated_data = validate_extracted_recipe(raw_extracted)

        # Check for duplicates
        existing = (
            db.session.query(Recipe)
            .filter(func.lower(Recipe.title) == validated_data["title"].lower())
            .first()
        )
        
        if existing:
            return jsonify({
                "error": f"A recipe with the title '{validated_data['title']}' already exists (ID: {existing.id})."
            }), 409

        # Best effort: a missing or broken photo never stops the recipe from being saved.
        # Done after the duplicate check so we don't download a photo for a recipe we reject.
        image_filename = fetch_and_store_image(image_candidates)

        # Save to database
        new_recipe = Recipe(**validated_data, image_filename=image_filename)

        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except ValueError as ve:
        db.session.rollback()
        delete_recipe_image(image_filename)
        # Gracefully catches our "has_recipe is false" errors and missing transcripts
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        delete_recipe_image(image_filename)
        return jsonify({"error": str(e)}), 500