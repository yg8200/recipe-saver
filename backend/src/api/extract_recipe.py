from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.core.database import db
from src.models.recipe import Recipe
from src.services.ai_extractor import extract_recipe_from_text
from src.services.scraper import scrape_recipe_page
from src.services.youtube_extractor import extract_recipe_from_youtube

extract_recipe_bp = Blueprint("extract_recipe", __name__)

@extract_recipe_bp.post("/recipes/extract")
def extract_recipe():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "The 'url' field is required in the JSON body"}), 400

    try:
        # Check if the URL is a YouTube link
        if "youtube.com" in url or "youtu.be" in url:
            extracted = extract_recipe_from_youtube(url)
            # The YouTube extractor returns a dict, so we map it
            clean_title = extracted.get("title", "YouTube Recipe").strip()
            ingredients = extracted.get("ingredients", [])
            instructions = extracted.get("instructions", [])
            prep_time = extracted.get("prep_time")
            cook_time = extracted.get("cook_time")
            servings = extracted.get("servings")
        else:
            # Standard webpage scraping
            raw_text = scrape_recipe_page(url)
            extracted_obj = extract_recipe_from_text(raw_text)
            # Assuming extract_recipe_from_text returns an object (like a Pydantic model) based on your existing code
            clean_title = extracted_obj.title.strip()
            ingredients = extracted_obj.ingredients
            instructions = extracted_obj.instructions
            prep_time = extracted_obj.prep_time_minutes
            cook_time = extracted_obj.cook_time_minutes
            servings = extracted_obj.servings

        # Check for duplicate extracted title
        existing = (
            db.session.query(Recipe)
            .filter(func.lower(Recipe.title) == clean_title.lower())
            .first()
        )
        
        if existing:
            return jsonify({
                "error": f"A recipe with the title '{clean_title}' already exists (ID: {existing.id})."
            }), 409

        # Save to database
        new_recipe = Recipe(
            title=clean_title,
            ingredients=ingredients,
            instructions=instructions,
            prep_time_minutes=prep_time,
            cook_time_minutes=cook_time,
            servings=servings,
        )

        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except ValueError as ve:
        # Catch specific value errors (like missing transcripts)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500