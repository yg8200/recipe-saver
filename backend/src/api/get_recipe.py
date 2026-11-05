from flask import Blueprint, jsonify
from src.core.database import db
from src.models.recipe import Recipe

get_recipe_bp = Blueprint("get_recipe", __name__)


@get_recipe_bp.route("/recipes", methods=["GET"])
def get_all_recipes():
    recipes = Recipe.query.all()
    return jsonify([recipe.to_dict() for recipe in recipes]), 200


@get_recipe_bp.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe_by_id(recipe_id: int):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    return jsonify(recipe.to_dict()), 200