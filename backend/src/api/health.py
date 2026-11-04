from flask import Blueprint, jsonify

# 1. Define the blueprint
# "health" is the internal name, __name__ helps locate resources
health_bp = Blueprint("health", __name__)

# 2. Register routes directly onto the blueprint instead of "app"
@health_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "recipe-saver-backend"
    }), 200