import os
import time
import logging
from pythonjsonlogger import jsonlogger
from flask import Flask, jsonify, request, render_template
import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor

# Configuración de logging
logger = logging.getLogger("todo-api")
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

app = Flask(__name__)

# Configuración de base de datos
DB_HOST = os.getenv("DB_HOST", "db-tareas")
DB_NAME = os.getenv("DB_NAME", "tareas_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS")

# Validar contraseña (Security Hotspot fix)
if not DB_PASS:
    logger.warning("DB_PASS no configurado. Usando valor por defecto (SOLO PARA DESARROLLO)")
    DB_PASS = "password"


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Base de datos inicializada correctamente.")
    except Error as exc:
        logger.error("No se pudo conectar a la base de datos: %s", exc)
        raise


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tasks", methods=["GET"])
def list_tasks():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, content, completed, created_at FROM tasks ORDER BY created_at DESC;"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Error as exc:
        logger.error("Error obteniendo tareas: %s", exc)
        return jsonify({"error": "Error interno"}), 500


@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "Contenido obligatorio"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO tasks (content) VALUES (%s) RETURNING *;",
            (data["content"],)
        )
        new_task = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Nueva tarea creada con ID: %s", new_task['id'])
        return jsonify(new_task), 201
    except Error as exc:
        logger.error("Error al guardar: %s", exc)
        return jsonify({"error": "Error al guardar"}), 500


@app.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json()

    if not data or "completed" not in data:
        return jsonify({"error": "Campo completed obligatorio"}), 400

    completed = data["completed"]

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE tasks SET completed = %s WHERE id = %s",
            (completed, task_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Tarea %s actualizada", task_id)
        return jsonify({"status": "updated"})
    except Error as exc:
        logger.error("Error al actualizar tarea %s: %s", task_id, exc)
        return jsonify({"error": "No se pudo actualizar"}), 500


def run_app():
    time.sleep(5)
    init_db()
    # Security: configurar host desde variable de entorno
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_app()
