import os
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import (
    Flask,
    jsonify,
    render_template,
    render_template_string,
    send_from_directory,
    request,
)
from flask_cors import CORS
from marshmallow import Schema, fields

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
CORS(app)  # Enable CORS for API endpoints


# In-memory storage for todos (in production, use a database)
todos_db = [
    {"id": 1, "title": "Finish this task", "status": False},
    {"id": 2, "title": "Finish that task", "status": True},
]
next_id = 3


@app.route("/")
def index():
    """Render the main GUI"""
    return render_template("index.html")


spec = APISpec(
    title="flask-api-swagger-doc",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


@app.route("/api/swagger.json")
def create_swagger_spec():
    return jsonify(spec.to_dict())


class TodoResponseSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    status = fields.Boolean()


class TodoListResponseSchema(Schema):
    todo_list = fields.List(fields.Nested(TodoResponseSchema))


@app.route("/todo")
def todo():
    """Get List of Todo (Legacy endpoint)
    ---
    get:
        description: Get List of Todos
        responses:
            200:
                description: Return a todo list
                content:
                    application/json:
                        schema: TodoListResponseSchema
    """
    return TodoListResponseSchema().dump({"todo_list": todos_db})


@app.route("/api/todo", methods=["GET"])
def get_todos():
    """Get all todos (API endpoint for GUI)"""
    return jsonify({"todo_list": todos_db})


@app.route("/api/todo", methods=["POST"])
def create_todo():
    """Create a new todo"""
    global next_id
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Title is required"}), 400

    new_todo = {"id": next_id, "title": data["title"], "status": False}
    todos_db.append(new_todo)
    next_id += 1

    return jsonify(new_todo), 201


@app.route("/api/todo/<int:todo_id>", methods=["PATCH"])
def update_todo(todo_id):
    """Update a todo (toggle status or update title)"""
    todo = next((t for t in todos_db if t["id"] == todo_id), None)

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    data = request.get_json()
    if "status" in data:
        todo["status"] = data["status"]
    if "title" in data:
        todo["title"] = data["title"]

    return jsonify(todo)


@app.route("/api/todo/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    """Delete a todo"""
    global todos_db
    todo = next((t for t in todos_db if t["id"] == todo_id), None)

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    todos_db = [t for t in todos_db if t["id"] != todo_id]
    return jsonify({"message": "Todo deleted successfully"}), 200


with app.test_request_context():
    spec.path(view=todo)


@app.route("/docs")
@app.route("/docs/<path:path>")
def swagger_docs(path=None):
    """Swagger documentation endpoint"""
    if not path or path == "index.html":
        # Render Swagger UI template with proper base_url
        template_path = os.path.join(BASE_DIR, "Swagger", "template", "index.html")
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
        return render_template_string(template_content, base_url="/docs")
    else:
        static_dir = os.path.join(BASE_DIR, "Swagger", "static")
        return send_from_directory(static_dir, path)


if __name__ == "__main__":
    app.run(debug=True)
