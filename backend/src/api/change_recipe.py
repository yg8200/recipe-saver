from flask import Blueprint, request, jsonify
from src.api.add_recipe import RECIPES

change_recipe_bp = Blueprint("change_recipe", __name__)


@change_recipe_bp.route("/recipes/<int:recipe_id>", methods=["PUT", "PATCH"])
def update_recipe(recipe_id: int):
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object"}), 400

    target_recipe = None
    for recipe in RECIPES:
        if recipe["id"] == recipe_id:
            target_recipe = recipe
            break

    if target_recipe is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    # Validate title if present in payload
    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            return jsonify({"error": "'title' must be a non-empty string"}), 400
        target_recipe["title"] = title.strip()

    # Validate ingredients if present in payload
    if "ingredients" in data:
        ingredients = data["ingredients"]
        if not isinstance(ingredients, list) or len(ingredients) == 0:
            return jsonify({"error": "'ingredients' must be a non-empty list"}), 400
        target_recipe["ingredients"] = ingredients

    # Validate instructions if present in payload
    if "instructions" in data:
        instructions = data["instructions"]
        if not isinstance(instructions, list) or len(instructions) == 0:
            return jsonify({"error": "'instructions' must be a non-empty list"}), 400
        target_recipe["instructions"] = instructions

    # Update optional numeric fields if present in payload
    for field in ["prep_time_minutes", "cook_time_minutes", "servings"]:
        if field in data:
            val = data[field]
            if val is not None and (not isinstance(val, int) or isinstance(val, bool) or val < 0):
                return jsonify({"error": f"'{field}' must be a non-negative integer or null"}), 400
            target_recipe[field] = val

    return jsonify(target_recipe), 200