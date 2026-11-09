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

    # Validate everything first and only then touch the recipe, so a rejected
    # request never leaves half-applied changes in the session.
    updates = {}

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            return jsonify({"error": "'title' must be a non-empty string"}), 400
        updates["title"] = title.strip()

    for field in ["ingredients", "instructions"]:
        if field in data:
            value = data[field]
            if not isinstance(value, list) or len(value) == 0:
                return jsonify({"error": f"'{field}' must be a non-empty list"}), 400
            updates[field] = value

    for field in ["prep_time_minutes", "cook_time_minutes", "servings"]:
        if field in data:
            val = data[field]
            if val is not None and (not isinstance(val, int) or isinstance(val, bool) or val < 0):
                return jsonify({"error": f"'{field}' must be a non-negative integer or null"}), 400
            updates[field] = val

    if "title" in updates:
        existing = (
            db.session.query(Recipe)
            .filter(func.lower(Recipe.title) == updates["title"].lower(), Recipe.id != recipe_id)
            .first()
        )
        if existing:
            return jsonify({"error": f"A recipe with the title '{updates['title']}' already exists."}), 409

    for field, value in updates.items():
        setattr(recipe, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A recipe with this title already exists."}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(recipe.to_dict()), 200