from flask import Blueprint, request, jsonify
from src.core.database import db
from src.models.recipe import Recipe

add_recipe_bp = Blueprint("add_recipe", __name__)


@add_recipe_bp.route("/recipes", methods=["POST"])
def add_recipe():
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    title = data.get("title")
    ingredients = data.get("ingredients")
    instructions = data.get("instructions")

    if not title or not isinstance(title, str) or not title.strip():
        return jsonify({"error": "'title' is required and must be a non-empty string"}), 400

    if not isinstance(ingredients, list) or len(ingredients) == 0:
        return jsonify({"error": "'ingredients' is required and must be a non-empty list"}), 400

    if not isinstance(instructions, list) or len(instructions) == 0:
        return jsonify({"error": "'instructions' is required and must be a non-empty list"}), 400

    new_recipe = Recipe(
        title=title.strip(),
        ingredients=ingredients,
        instructions=instructions,
        prep_time_minutes=data.get("prep_time_minutes"),
        cook_time_minutes=data.get("cook_time_minutes"),
        servings=data.get("servings")
    )

    db.session.add(new_recipe)
    db.session.commit()

    return jsonify(new_recipe.to_dict()), 201