from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user=os.getenv("DB_USER", "root"),
        password=os.environ["DB_PASSWORD"],
        database="private"
    )


@app.route("/")
def home():
    return "November 13 backend is running!"


@app.route("/health")
def health():
    try:
        connection = get_db_connection()
        connection.close()

        return jsonify({
            "status": "success",
            "message": "Python connected to MySQL"
        })

    except (mysql.connector.Error, KeyError):
        app.logger.exception("Database connection failed")

        return jsonify({
            "status": "error",
            "message": "Database connection failed. Check server configuration."
        }), 500


@app.route("/api/answers", methods=["POST"])
def save_answers():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Please send answers as a JSON object."
        }), 400

    if not data:
        return jsonify({
            "status": "error",
            "message": "No answers were provided."
        }), 400

    if not all(
        isinstance(key, str) and isinstance(value, (str, int, float, bool, list, dict, type(None)))
        for key, value in data.items()
    ):
        return jsonify({
            "status": "error",
            "message": "Invalid answer format."
        }), 400

    connection = None
    cursor = None

    try:
        import json

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO questionnaire_answers (answers)
            VALUES (%s)
            """,
            (json.dumps(data, ensure_ascii=False),)
        )

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "Answers saved successfully."
        }), 201

    except (mysql.connector.Error, KeyError):
        app.logger.exception("Could not save questionnaire answers")

        return jsonify({
            "status": "error",
            "message": "Could not save answers. Check the server configuration."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(debug=False)