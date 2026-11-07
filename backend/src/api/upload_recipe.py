from flask import Blueprint, request, jsonify
from src.services.image_extractor import extract_recipe_from_image
from src.core.database import db
from src.models.recipe import Recipe

upload_recipe_bp = Blueprint('upload_recipe', __name__)

@upload_recipe_bp.route('/api/recipes/upload', methods=['POST'])
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
        
        # Fallback to detect HEIC from the filename if the browser/client didn't send the mime type properly
        if file.filename and file.filename.lower().endswith(('.heic', '.heif')):
            mime_type = 'image/heic'
        elif not mime_type:
            mime_type = 'image/jpeg'

        # Call the dedicated image extraction service
        extracted_data = extract_recipe_from_image(image_bytes, mime_type)

        # Removed 'description' to match your SQLAlchemy model
        new_recipe = Recipe(
            title=extracted_data.get("title", "Untitled Recipe"),
            ingredients=extracted_data.get("ingredients", []),
            instructions=extracted_data.get("instructions", []),
            prep_time_minutes=extracted_data.get("prep_time"),
            cook_time_minutes=extracted_data.get("cook_time"),
            servings=extracted_data.get("servings")
        )
        
        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500