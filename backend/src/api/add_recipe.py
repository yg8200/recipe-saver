from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.core.database import db
from src.models.recipe import Recipe

add_recipe_bp = Blueprint("add_recipe", __name__)


@add_recipe_bp.post("/recipes")
def add_recipe():
    # silent=True: return our own 400 instead of Flask's 415
    data = request.get_json(silent=True)
    
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "'title' is required"}), 400
    
    title = title.strip()

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
    if not isinstance(ingredients, list) or len(ingredients) == 0:
        return jsonify({"error": "'ingredients' is required"}), 400

    instructions = data.get("instructions")
    if not isinstance(instructions, list) or len(instructions) == 0:
        return jsonify({"error": "'instructions' is required"}), 400

    for field in ["prep_time_minutes", "cook_time_minutes", "servings"]:
        val = data.get(field)
        # bool is a subclass of int
        if val is not None and (not isinstance(val, int) or isinstance(val, bool) or val < 0):
            return jsonify({"error": f"'{field}' must be a non-negative integer or null"}), 400

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