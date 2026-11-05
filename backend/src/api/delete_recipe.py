from flask import Blueprint, jsonify
from src.core.database import db
from src.models.recipe import Recipe

delete_recipe_bp = Blueprint("delete_recipe", __name__)


@delete_recipe_bp.route("/recipes/<int:recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id: int):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    deleted_data = recipe.to_dict()
    db.session.delete(recipe)
    db.session.commit()

    return jsonify({
        "message": "Recipe deleted successfully",
        "deleted_recipe": deleted_data
    }), 200