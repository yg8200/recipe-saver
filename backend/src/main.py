from flask import Flask, jsonify

# 1. Initialize the Flask application instance
app = Flask(__name__)

# 2. Define a root health-check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "recipe-saver-backend"
    }), 200

# 3. Run the development server when executed directly
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)