from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.core.database import db
from src.models.recipe import Recipe

add_recipe_bp = Blueprint("add_recipe", __name__)


@add_recipe_bp.post("/recipes")
def add_recipe():
  data = request.get_json() or {}

  title = (data.get("title") or "").strip()
  if not title:
    return jsonify({"error": "The 'title' field is required"}), 400

  # Check if a recipe with this title already exists (case-insensitive)
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
  instructions = data.get("instructions")

  if not isinstance(ingredients, list) or not isinstance(instructions, list):
    return (
        jsonify(
            {"error": "'ingredients' and 'instructions' must be valid lists"}
        ),
        400,
    )

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