from flask import Blueprint, request, jsonify
from src.core.database import db
from src.models.recipe import Recipe
from src.services.scraper import scrape_recipe_page
from src.services.ai_extractor import extract_recipe_from_text

extract_recipe_bp = Blueprint("extract_recipe", __name__)


@extract_recipe_bp.post("/recipes/extract")
def extract_recipe():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "The 'url' field is required in the JSON body"}), 400

    try:
        # 1. Scrape and clean webpage text
        raw_text = scrape_recipe_page(url)

        # 2. Extract recipe data with OpenAI
        extracted = extract_recipe_from_text(raw_text)

        # 3. Create database entity
        new_recipe = Recipe(
            title=extracted.title,
            ingredients=extracted.ingredients,
            instructions=extracted.instructions,
            prep_time_minutes=extracted.prep_time_minutes,
            cook_time_minutes=extracted.cook_time_minutes,
            servings=extracted.servings,
        )

        # 4. Save to PostgreSQL
        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500