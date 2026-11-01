from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)


@app.route("/")
def index():
    """Display unanswered StackOverflow questions"""
    try:
        response = requests.get(
            "https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow",
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        questions = []

        for item in data.get("items", []):
            if item.get("answer_count", 0) == 0:
                questions.append(
                    {
                        "title": item.get("title", "No title"),
                        "link": item.get("link", "#"),
                    }
                )

        return render_template(
            "index.html", questions=questions, total_questions=len(questions)
        )

    except requests.RequestException as e:
        return (
            jsonify(
                {"success": False, "error": f"Failed to fetch questions: {str(e)}"}
            ),
            500,
        )


@app.route("/api/questions")
def api_questions():
    """API endpoint to get unanswered questions as JSON"""
    try:
        response = requests.get(
            "https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow",
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        questions = []

        for item in data.get("items", []):
            if item.get("answer_count", 0) == 0:
                questions.append(
                    {
                        "title": item.get("title", "No title"),
                        "link": item.get("link", "#"),
                        "tags": item.get("tags", []),
                        "score": item.get("score", 0),
                        "creation_date": item.get("creation_date", 0),
                    }
                )

        return jsonify(
            {"success": True, "count": len(questions), "questions": questions}
        )

    except requests.RequestException as e:
        return (
            jsonify(
                {"success": False, "error": f"Failed to fetch questions: {str(e)}"}
            ),
            500,
        )


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
