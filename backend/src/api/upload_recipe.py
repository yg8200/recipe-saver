import logging

from flask import Blueprint, request, jsonify
from sqlalchemy import func
from src.services.image_extractor import extract_recipe_from_image
from src.services.recipe_corrector import correct_recipe_text
from src.api.extract_recipe import validate_extracted_recipe  # deterministic guardrail
from src.core.database import db
from src.models.recipe import Recipe

logger = logging.getLogger(__name__)

upload_recipe_bp = Blueprint('upload_recipe', __name__)

@upload_recipe_bp.route('/recipes/upload', methods=['POST'])
def upload_recipe_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    try:
        # Read the image data
        image_bytes = file.read()
        mime_type = file.mimetype
        
        # Fallback to detect HEIC from the filename
        if file.filename and file.filename.lower().endswith(('.heic', '.heif')):
            mime_type = 'image/heic'
        elif not mime_type:
            mime_type = 'image/jpeg'

        # 1. Read the text from the image (Gemini)
        raw_extracted_data = extract_recipe_from_image(image_bytes, mime_type)

        # 2. AI guardrail: fix OCR typos with the configured corrector model
        # If the corrector fails (API error, bad JSON, wrong shape), fall back to the raw OCR result
        # instead of failing the whole upload.
        try:
            corrected_data = correct_recipe_text(raw_extracted_data)
            if not isinstance(corrected_data, dict):
                raise ValueError("Corrector did not return a JSON object")
            validate_extracted_recipe(corrected_data)
        except Exception:
            logger.warning("Recipe correction failed; saving uncorrected OCR text", exc_info=True)
            corrected_data = raw_extracted_data

        # 3. Deterministic guardrail: make sure the output is valid before it reaches the DB
        validated_data = validate_extracted_recipe(corrected_data)

        # Reject duplicates (same title, case-insensitive)
        existing = (
            db.session.query(Recipe)
            .filter(func.lower(Recipe.title) == validated_data["title"].lower())
            .first()
        )
        if existing:
            return jsonify({
                "error": f"A recipe with the title '{validated_data['title']}' already exists."
            }), 409

        # Save to the database
        new_recipe = Recipe(
            title=validated_data["title"],
            ingredients=validated_data["ingredients"],
            instructions=validated_data["instructions"],
            prep_time_minutes=validated_data["prep_time_minutes"],
            cook_time_minutes=validated_data["cook_time_minutes"],
            servings=validated_data["servings"],
        )
        
        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except ValueError as ve:
        # Guardrail errors are the user's problem to see (400)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500