from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.exceptions import NotFound

from src.core.database import db
from src.models.recipe import Recipe
from src.services.image_store import delete_recipe_image, save_recipe_image, upload_dir

recipe_image_bp = Blueprint("recipe_image", __name__)

# Stored names are random and a changed photo gets a NEW name, so a file never changes
# under its URL. That makes it safe for browsers to cache for a year.
ONE_YEAR = 60 * 60 * 24 * 365


@recipe_image_bp.post("/recipes/<int:recipe_id>/image")
def set_recipe_image(recipe_id: int):
    """Adds or replaces the dish photo. Send multipart/form-data with the file in field 'image'."""
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    file = request.files.get("image")
    if file is None or file.filename == "":
        return jsonify({"error": "No image file provided"}), 400

    try:
        new_filename = save_recipe_image(file.read())
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    old_filename = recipe.image_filename
    recipe.image_filename = new_filename
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        delete_recipe_image(new_filename)  # don't leave an orphan file behind
        return jsonify({"error": str(e)}), 500

    # Only after the database points at the new file is it safe to remove the old one
    delete_recipe_image(old_filename)
    return jsonify(recipe.to_dict()), 200


@recipe_image_bp.delete("/recipes/<int:recipe_id>/image")
def remove_recipe_image(recipe_id: int):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": f"Recipe with id {recipe_id} not found"}), 404

    old_filename = recipe.image_filename
    recipe.image_filename = None
    db.session.commit()
    delete_recipe_image(old_filename)
    return jsonify(recipe.to_dict()), 200


@recipe_image_bp.get("/images/<path:filename>")
def get_image(filename: str):
    try:
        # send_from_directory refuses paths that escape the folder (e.g. "../.env")
        return send_from_directory(upload_dir(), filename, max_age=ONE_YEAR)
    except NotFound:
        return jsonify({"error": "Image not found"}), 404
