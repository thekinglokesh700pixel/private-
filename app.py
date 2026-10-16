from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import Json
import os

app = Flask(__name__)


def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return psycopg2.connect(database_url)


@app.route("/")
def home():
    return "November 13 backend is running!"


@app.route("/health")
def health():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return jsonify({
            "status": "success",
            "message": "Python connected to PostgreSQL"
        })

    except Exception:
        app.logger.exception("Database connection failed")

        return jsonify({
            "status": "error",
            "message": "Database connection failed. Check server logs."
        }), 500

    finally:
        if connection is not None:
            connection.close()


@app.route("/api/answers", methods=["POST"])
def save_answers():
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({
            "status": "error",
            "message": "Please send answers as a non-empty JSON object."
        }), 400

    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questionnaire_answers (
                    id BIGSERIAL PRIMARY KEY,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    answers JSONB NOT NULL
                )
            """)

            cursor.execute(
                """
                INSERT INTO questionnaire_answers (answers)
                VALUES (%s)
                RETURNING id
                """,
                (Json(data),)
            )

            answer_id = cursor.fetchone()[0]

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "Answers saved successfully.",
            "id": answer_id
        }), 201

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Could not save questionnaire answers")

        return jsonify({
            "status": "error",
            "message": "Could not save answers. Check server logs."
        }), 500

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )
