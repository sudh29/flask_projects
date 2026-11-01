import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initial store data
stores = [
    {"name": "beautiful store", "items": [{"name": "flowers", "price": 100}]},
    {"name": "beautiful store 2", "items": [{"name": "books", "price": 100}]},
]


# Helper functions
def find_store(store_name):
    """Find a store by name."""
    return next((store for store in stores if store["name"] == store_name), None)


def error_response(message, status_code):
    """Return a consistent error response."""
    return jsonify({"error": message, "success": False}), status_code


def success_response(data, status_code=200):
    """Return a consistent success response."""
    response = {"success": True}
    response.update(data)
    return jsonify(response), status_code


# Routes
@app.route("/")
def home():
    """Serve the interactive testing page."""
    return send_file(os.path.join(BASE_DIR, "index.html"))


@app.route("/api")
def api_info():
    """API information endpoint."""
    return jsonify(
        {
            "message": "Welcome to Flask Store API",
            "version": "1.0.0",
            "endpoints": {
                "stores": "/store",
                "create_store": "/store [POST]",
                "get_store": "/store/<name>",
                "delete_store": "/store/<name> [DELETE]",
                "store_items": "/store/<name>/item",
                "add_item": "/store/<name>/item [POST]",
            },
        }
    )


@app.route("/store", methods=["GET"])
def get_all_stores():
    """Get all stores."""
    return success_response({"stores": stores, "count": len(stores)})


@app.route("/store", methods=["POST"])
def create_store():
    """Create a new store."""
    if not request.is_json:
        return error_response("Content-Type must be application/json", 415)

    request_data = request.get_json()

    # Validate input
    if not request_data or "name" not in request_data:
        return error_response("Store name is required", 400)

    store_name = request_data["name"].strip()

    if not store_name:
        return error_response("Store name cannot be empty", 400)

    # Check if store already exists
    if find_store(store_name):
        return error_response(f"Store '{store_name}' already exists", 409)

    new_store = {"name": store_name, "items": []}
    stores.append(new_store)

    return success_response({"store": new_store}, 201)


@app.route("/store/<string:name>", methods=["GET"])
def get_store(name):
    """Get a specific store by name."""
    store = find_store(name)

    if not store:
        return error_response(f"Store '{name}' not found", 404)

    return success_response({"store": store})


@app.route("/store/<string:name>", methods=["DELETE"])
def delete_store(name):
    """Delete a store by name."""
    store = find_store(name)

    if not store:
        return error_response(f"Store '{name}' not found", 404)

    stores.remove(store)
    return success_response({"message": f"Store '{name}' deleted successfully"})


@app.route("/store/<string:name>/item", methods=["GET"])
def get_store_items(name):
    """Get all items in a store."""
    store = find_store(name)

    if not store:
        return error_response(f"Store '{name}' not found", 404)

    return success_response(
        {"store": name, "items": store["items"], "count": len(store["items"])}
    )


@app.route("/store/<string:name>/item", methods=["POST"])
def create_store_item(name):
    """Add an item to a store."""
    store = find_store(name)

    if not store:
        return error_response(f"Store '{name}' not found", 404)

    if not request.is_json:
        return error_response("Content-Type must be application/json", 415)

    request_data = request.get_json()

    # Validate input
    if not request_data:
        return error_response("Request body is required", 400)

    if "name" not in request_data:
        return error_response("Item name is required", 400)

    if "price" not in request_data:
        return error_response("Item price is required", 400)

    item_name = request_data["name"].strip()

    if not item_name:
        return error_response("Item name cannot be empty", 400)

    try:
        price = float(request_data["price"])
        if price < 0:
            return error_response("Price must be a positive number", 400)
    except (ValueError, TypeError):
        return error_response("Price must be a valid number", 400)

    # Check if item already exists in store
    if any(item["name"] == item_name for item in store["items"]):
        return error_response(
            f"Item '{item_name}' already exists in store '{name}'", 409
        )

    new_item = {"name": item_name, "price": price}
    store["items"].append(new_item)

    return success_response({"item": new_item, "store": name}, 201)


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return error_response("Resource not found", 404)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return error_response("Internal server error", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
