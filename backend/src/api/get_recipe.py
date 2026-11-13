import random

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import selectinload
from src.core.database import db
from src.models.recipe import Recipe

get_recipe_bp = Blueprint("get_recipe", __name__)


@get_recipe_bp.route("/recipes", methods=["GET"])
def get_all_recipes():
    # Oldest first (by id), so the list reads in the order recipes were saved.
    # selectinload fetches every recipe's folders in ONE extra query (avoids the N+1 problem).
    query = Recipe.query.options(selectinload(Recipe.folders))

    # Query-string values are always text (or None when the parameter is missing)
    raw = request.args.get("min_rating")
    if raw is not None:
        error = jsonify({"error": "'min_rating' must be an integer from 1 to 5"}), 400
        try:
            min_rating = int(raw)
        except ValueError:
            return error
        if not 1 <= min_rating <= 5:
            return error
        # Unrated recipes have rating NULL; "NULL >= 4" is never true, so they are left out
        query = query.filter(Recipe.rating >= min_rating)

    recipes = query.order_by(Recipe.id.asc()).all()
    return jsonify([recipe.to_dict() for recipe in recipes]), 200


@get_recipe_bp.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe_by_id(recipe_id: int):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    return jsonify(recipe.to_dict()), 200


@get_recipe_bp.route("/recipes/random", methods=["GET"])
def get_random_recipe():
    db_ids = Recipe.query.with_entities(Recipe.id).all()
    if not db_ids:
        return jsonify({"error": "No recipes found"}), 404

    random_id = random.choice(db_ids).id
    random_recipe = db.session.get(Recipe, random_id)
    return jsonify(random_recipe.to_dict()), 200
