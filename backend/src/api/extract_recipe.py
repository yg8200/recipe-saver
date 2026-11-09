from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.core.database import db
from src.models.recipe import Recipe

# Ensure these imports match your actual file names
from src.services.scraper import scrape_recipe_page
from src.services.ai_extractor import extract_recipe_from_text
from src.services.youtube_extractor import extract_recipe_from_youtube

extract_recipe_bp = Blueprint("extract_recipe", __name__)

def validate_extracted_recipe(data: dict) -> dict:
    """Validates and cleans the AI extracted recipe data."""
    if not isinstance(data, dict):
        raise ValueError("AI did not return a valid JSON object.")

    title = data.get("title")
    if not title or not isinstance(title, str) or title.strip() == "":
        raise ValueError("Extraction failed: Could not find a valid recipe title.")

    ingredients = data.get("ingredients")
    if not isinstance(ingredients, list) or len(ingredients) == 0:
        raise ValueError("Extraction failed: No ingredients were found in this source.")

    instructions = data.get("instructions")
    if not isinstance(instructions, list) or len(instructions) == 0:
        raise ValueError("Extraction failed: No instructions were found in this source.")

    return {
        "title": title.strip(),
        "ingredients": [str(i).strip() for i in ingredients if str(i).strip()],
        "instructions": [str(i).strip() for i in instructions if str(i).strip()],
        "prep_time_minutes": data.get("prep_time") if isinstance(data.get("prep_time"), int) else None,
        "cook_time_minutes": data.get("cook_time") if isinstance(data.get("cook_time"), int) else None,
        "servings": data.get("servings") if isinstance(data.get("servings"), int) else None,
    }


@extract_recipe_bp.post("/recipes/extract")
def extract_recipe():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "The 'url' field is required in the JSON body"}), 400

    try:
        # Route to the correct extraction service
        if "youtube.com" in url or "youtu.be" in url:
            # The YouTube extractor now handles description vs transcript logic internally
            raw_extracted = extract_recipe_from_youtube(url)
        else:
            # Standard webpage scraping
            raw_text = scrape_recipe_page(url)
            raw_extracted = extract_recipe_from_text(raw_text)

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

        # Save to database
        new_recipe = Recipe(**validated_data)

        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except ValueError as ve:
        # Gracefully catches our "has_recipe is false" errors and missing transcripts
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500