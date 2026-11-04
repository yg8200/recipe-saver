from flask import Blueprint, jsonify
from src.api.add_recipe import RECIPES

delete_recipe_bp = Blueprint("delete_recipe", __name__)

@delete_recipe_bp.route("/recipes/<int:recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id: int):
    recipe_index = None

    for index, recipe in enumerate(RECIPES):
        if recipe["id"] == recipe_id:
            recipe_index = index
            break

    if recipe_index is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    deleted_recipe = RECIPES.pop(recipe_index)

    return jsonify({
        "message": "Recipe deleted successfully",
        "deleted_recipe": deleted_recipe
    }), 200