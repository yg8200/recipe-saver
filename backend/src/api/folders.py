from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.core.database import db
from src.models.folder import Folder
from src.models.recipe import Recipe

folders_bp = Blueprint("folders", __name__)

MAX_NAME_LENGTH = 100


def _read_name():
    """Return (name, error_response). Exactly one of them is None."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Request body must be a valid JSON object"}), 400)
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return None, (jsonify({"error": "'name' is required"}), 400)
    name = name.strip()
    if len(name) > MAX_NAME_LENGTH:
        return None, (jsonify({"error": f"'name' must be at most {MAX_NAME_LENGTH} characters"}), 400)
    return name, None


def _name_taken(name: str, ignore_id: int | None = None) -> bool:
    # Case-insensitive, like recipe titles, so "Grandma" and "grandma" are the same folder
    query = db.session.query(Folder).filter(func.lower(Folder.name) == name.lower())
    if ignore_id is not None:
        query = query.filter(Folder.id != ignore_id)
    return query.first() is not None


def _not_found(kind: str, item_id: int):
    return jsonify({"error": f"{kind} with id {item_id} not found"}), 404


@folders_bp.get("/folders")
def list_folders():
    folders = Folder.query.order_by(Folder.name.asc()).all()
    return jsonify([folder.to_dict() for folder in folders]), 200


@folders_bp.post("/folders")
def create_folder():
    name, error = _read_name()
    if error:
        return error
    if _name_taken(name):
        return jsonify({"error": f"A folder with the name '{name}' already exists."}), 409

    folder = Folder(name=name)
    db.session.add(folder)
    db.session.commit()
    return jsonify(folder.to_dict()), 201


@folders_bp.patch("/folders/<int:folder_id>")
def rename_folder(folder_id: int):
    folder = db.session.get(Folder, folder_id)
    if folder is None:
        return _not_found("Folder", folder_id)
    name, error = _read_name()
    if error:
        return error
    if _name_taken(name, ignore_id=folder_id):
        return jsonify({"error": f"A folder with the name '{name}' already exists."}), 409

    folder.name = name
    db.session.commit()
    return jsonify(folder.to_dict()), 200


@folders_bp.delete("/folders/<int:folder_id>")
def delete_folder(folder_id: int):
    folder = db.session.get(Folder, folder_id)
    if folder is None:
        return _not_found("Folder", folder_id)

    deleted = folder.to_dict()
    # Deleting the folder removes only its links; the recipes stay in the app
    db.session.delete(folder)
    db.session.commit()
    return jsonify({"message": "Folder deleted successfully", "deleted_folder": deleted}), 200


# PUT is idempotent: adding a recipe that is already in the folder is a harmless no-op (still 200).
@folders_bp.put("/folders/<int:folder_id>/recipes/<int:recipe_id>")
def add_recipe_to_folder(folder_id: int, recipe_id: int):
    folder = db.session.get(Folder, folder_id)
    if folder is None:
        return _not_found("Folder", folder_id)
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return _not_found("Recipe", recipe_id)

    if folder not in recipe.folders:
        recipe.folders.append(folder)
        db.session.commit()
    return jsonify(recipe.to_dict()), 200


@folders_bp.delete("/folders/<int:folder_id>/recipes/<int:recipe_id>")
def remove_recipe_from_folder(folder_id: int, recipe_id: int):
    folder = db.session.get(Folder, folder_id)
    if folder is None:
        return _not_found("Folder", folder_id)
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return _not_found("Recipe", recipe_id)

    if folder in recipe.folders:
        recipe.folders.remove(folder)
        db.session.commit()
    return jsonify(recipe.to_dict()), 200
