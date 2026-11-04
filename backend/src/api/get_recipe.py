from flask import Blueprint, jsonify
from src.api.add_recipe import RECIPES

get_recipe_bp = Blueprint("get_recipe", __name__)


@get_recipe_bp.route("/recipes", methods=["GET"])
def get_all_recipes():
    return jsonify(RECIPES), 200


@get_recipe_bp.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe_by_id(recipe_id: int):
    for recipe in RECIPES:
        if recipe["id"] == recipe_id:
            return jsonify(recipe), 200

    return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404