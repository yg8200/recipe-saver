from flask import Blueprint, request, jsonify
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from src.core.database import db
from src.models.recipe import Recipe

change_recipe_bp = Blueprint("change_recipe", __name__)


@change_recipe_bp.route("/recipes/<int:recipe_id>", methods=["PUT", "PATCH"])
def update_recipe(recipe_id: int):
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            return jsonify({"error": "'title' must be a non-empty string"}), 400
        title = title.strip()
        existing = (
            db.session.query(Recipe)
            .filter(func.lower(Recipe.title) == title.lower(), Recipe.id != recipe_id)
            .first()
        )
        if existing:
            return jsonify({"error": f"A recipe with the title '{title}' already exists."}), 409
        recipe.title = title

    if "ingredients" in data:
        ingredients = data["ingredients"]
        if not isinstance(ingredients, list) or len(ingredients) == 0:
            return jsonify({"error": "'ingredients' must be a non-empty list"}), 400
        recipe.ingredients = ingredients

    if "instructions" in data:
        instructions = data["instructions"]
        if not isinstance(instructions, list) or len(instructions) == 0:
            return jsonify({"error": "'instructions' must be a non-empty list"}), 400
        recipe.instructions = instructions

    for field in ["prep_time_minutes", "cook_time_minutes", "servings"]:
        if field in data:
            val = data[field]
            if val is not None and (not isinstance(val, int) or isinstance(val, bool) or val < 0):
                return jsonify({"error": f"'{field}' must be a non-negative integer or null"}), 400
            setattr(recipe, field, val)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A recipe with this title already exists."}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(recipe.to_dict()), 200