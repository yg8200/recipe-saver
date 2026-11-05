from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.core.database import db
from src.models.recipe import Recipe
from src.services.ai_extractor import extract_recipe_from_text
from src.services.scraper import scrape_recipe_page

extract_recipe_bp = Blueprint("extract_recipe", __name__)


@extract_recipe_bp.post("/recipes/extract")
def extract_recipe():
  data = request.get_json() or {}
  url = data.get("url")

  if not url:
    return (
        jsonify({"error": "The 'url' field is required in the JSON body"}),
        400,
    )

  try:
    raw_text = scrape_recipe_page(url)
    extracted = extract_recipe_from_text(raw_text)

    # Check for duplicate extracted title
    clean_title = extracted.title.strip()
    existing = (
        db.session.query(Recipe)
        .filter(func.lower(Recipe.title) == clean_title.lower())
        .first()
    )
    if existing:
      return (
          jsonify({
              "error": (
                  f"A recipe with the title '{clean_title}' already exists"
                  f" (ID: {existing.id})."
              )
          }),
          409,
      )

    new_recipe = Recipe(
        title=clean_title,
        ingredients=extracted.ingredients,
        instructions=extracted.instructions,
        prep_time_minutes=extracted.prep_time_minutes,
        cook_time_minutes=extracted.cook_time_minutes,
        servings=extracted.servings,
    )

    db.session.add(new_recipe)
    db.session.commit()

    return jsonify(new_recipe.to_dict()), 201

  except Exception as e:
    db.session.rollback()
    return jsonify({"error": str(e)}), 500