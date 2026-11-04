from flask import Blueprint, jsonify

change_recepie_bp = Blueprint("change_recepie", __name__)

@change_recepie_bp.route("/change-recepie/<int:recepie_id>", methods=["PATCH"])
def change_recepie(recepie_id):
    # Placeholder for changing a recipe logic
    return jsonify({
        "message": "Recipe changed successfully!"
    }), 200