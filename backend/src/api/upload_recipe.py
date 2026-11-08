from flask import Blueprint, request, jsonify
from sqlalchemy import func
from src.services.image_extractor import extract_recipe_from_image
from src.services.recipe_corrector import correct_recipe_text
from src.api.extract_recipe import validate_extracted_recipe  # ייבוא ה-Guardrail הדטרמיניסטי
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
        
        # Fallback to detect HEIC from the filename
        if file.filename and file.filename.lower().endswith(('.heic', '.heif')):
            mime_type = 'image/heic'
        elif not mime_type:
            mime_type = 'image/jpeg'

        # 1. חילוץ הטקסט מהתמונה (Gemini)
        raw_extracted_data = extract_recipe_from_image(image_bytes, mime_type)

        # 2. Guardrail מבוסס AI: תיקון השגיאות של ה-OCR באנגלית דרך gpt-4o-mini
        corrected_data = correct_recipe_text(raw_extracted_data)

        # 3. Guardrail דטרמיניסטי: מוודא שהפלט תקין לפני ה-DB
        validated_data = validate_extracted_recipe(corrected_data)

        # בדיקה האם המתכון כבר קיים במסד הנתונים כדי למנוע כפילויות (אופציונלי אבל מומלץ)
        existing = (
            db.session.query(Recipe)
            .filter(func.lower(Recipe.title) == validated_data["title"].lower())
            .first()
        )
        if existing:
            return jsonify({
                "error": f"A recipe with the title '{validated_data['title']}' already exists."
            }), 409

        # שמירה למסד הנתונים
        new_recipe = Recipe(
            title=validated_data.get("title", "Untitled Recipe"),
            ingredients=validated_data.get("ingredients", []),
            instructions=validated_data.get("instructions", []),
            prep_time_minutes=validated_data.get("prep_time_minutes"),
            cook_time_minutes=validated_data.get("cook_time_minutes"),
            servings=validated_data.get("servings")
        )
        
        db.session.add(new_recipe)
        db.session.commit()

        return jsonify(new_recipe.to_dict()), 201

    except ValueError as ve:
        # תופס שגיאות מה-Guardrail ומחזיר למשתמש
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500