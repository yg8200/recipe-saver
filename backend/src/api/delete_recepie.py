from flask import Blueprint, jsonify

delete_recepie_bp = Blueprint("delete_recepie", __name__)

@delete_recepie_bp.route("/delete-recepie/<int:recepie_id>", methods=["DELETE"])
def delete_recepie(recepie_id):
    # Placeholder for deleting a recipe logic
    return jsonify({
        "message": f"Recipe deleted successfully! ID: {recepie_id}"
    }), 200