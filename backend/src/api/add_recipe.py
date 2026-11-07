from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.core.database import db
from src.models.recipe import Recipe

add_recipe_bp = Blueprint("add_recipe", __name__)


@add_recipe_bp.post("/recipes")
def add_recipe():
    # Use silent=True to avoid Flask's automatic 415 error on bad content-types
    data = request.get_json(silent=True)
    
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    title = data.get("title")
    # Check if title exists, is a string, and isn't just empty spaces
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "'title' is required"}), 400
    
    title = title.strip()

    # Check if a recipe with this title already exists (case-insensitive)
    existing = (
        db.session.query(Recipe)
        .filter(func.lower(Recipe.title) == title.lower())
        .first()
    )
    if existing:
        return (
            jsonify({"error": f"A recipe with the title '{title}' already exists."}),
            409,
        )

    ingredients = data.get("ingredients")
    # Ensure ingredients is a list and has at least one item
    if not isinstance(ingredients, list) or len(ingredients) == 0:
        return jsonify({"error": "'ingredients' is required"}), 400

    instructions = data.get("instructions")
    # Ensure instructions is a list and has at least one item
    if not isinstance(instructions, list) or len(instructions) == 0:
        return jsonify({"error": "'instructions' is required"}), 400

    try:
        new_recipe = Recipe(
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            prep_time_minutes=data.get("prep_time_minutes"),
            cook_time_minutes=data.get("cook_time_minutes"),
            servings=data.get("servings"),
        )

        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500