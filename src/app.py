"""A small persistent task board, backed by SQLite."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

STATUSES = ("todo", "progress", "done")
PRIORITIES = ("low", "medium", "high")


def create_app(database=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    db_path = Path(database or os.environ.get("DATABASE_PATH", "data/tasks.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect():
        connection = sqlite3.connect(db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'todo',
                due_date TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
            )
        """)

    def validate(payload, partial=False):
        if not isinstance(payload, dict):
            raise ValueError("Send a JSON object.")
        allowed = {"title", "course", "notes", "priority", "status", "due_date"}
        if set(payload) - allowed:
            raise ValueError("Unknown task field.")
        if not partial and "title" not in payload:
            raise ValueError("A title is required.")
        result = {}
        for key, value in payload.items():
            if not isinstance(value, str):
                raise ValueError(f"{key} must be text.")
            value = value.strip()
            limits = {"title": 120, "course": 60, "notes": 1000}
            if key in limits and len(value) > limits[key]:
                raise ValueError(f"{key} must be at most {limits[key]} characters.")
            if key == "title" and not value:
                raise ValueError("A title is required.")
            if key == "status" and value not in STATUSES:
                raise ValueError("Choose a valid status.")
            if key == "priority" and value not in PRIORITIES:
                raise ValueError("Choose a valid priority.")
            if key == "due_date" and value:
                try:
                    if date.fromisoformat(value).isoformat() != value:
                        raise ValueError()
                except ValueError:
                    raise ValueError("Use a real date in YYYY-MM-DD format.") from None
            result[key] = value
        return result

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        with connect() as db:
            db.execute("SELECT id FROM tasks LIMIT 1").fetchone()
        return jsonify(status="ok", service="campus-taskboard")

    @app.get("/api/tasks")
    def list_tasks():
        with connect() as db:
            rows = db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return jsonify([dict(row) for row in rows])

    @app.post("/api/tasks")
    def add_task():
        try:
            values = validate(request.get_json())
        except ValueError as error:
            return jsonify(error=str(error)), 400
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        with connect() as db:
            cursor = db.execute(
                f"INSERT INTO tasks ({columns}) VALUES ({placeholders})", list(values.values())
            )
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify(dict(row)), 201

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id):
        try:
            values = validate(request.get_json(), partial=True)
        except ValueError as error:
            return jsonify(error=str(error)), 400
        with connect() as db:
            if db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone() is None:
                return jsonify(error="Task not found."), 404
            if values:
                setters = ", ".join(f"{key} = ?" for key in values)
                db.execute(f"UPDATE tasks SET {setters} WHERE id = ?", [*values.values(), task_id])
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return jsonify(dict(row))

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        with connect() as db:
            result = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if result.rowcount == 0:
            return jsonify(error="Task not found."), 404
        return "", 204

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error=error.description), error.code
        return error

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.path.startswith("/api/") or request.path == "/health":
            response.headers["Cache-Control"] = "no-store"
        return response

    return app
