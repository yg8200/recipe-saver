from flask import Blueprint, jsonify

add_recepie_bp = Blueprint("add_recepie", __name__)

@add_recepie_bp.route("/add-recepie", methods=["POST"])
def add_recepie():
    # Placeholder for adding a recipe logic
    return jsonify({
        "message": "Recipe added successfully!"
    }), 201