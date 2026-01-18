import os
import time
import logging
from pythonjsonlogger import jsonlogger
from flask import Flask, jsonify, request, render_template
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración de logs: Formato JSON profesional
logger = logging.getLogger("todo-api")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
logger.propagate = False

app = Flask(__name__)

# Configuración mediante variables de entorno
DB_HOST = os.getenv('DB_HOST', 'db-tareas')
DB_NAME = os.getenv('DB_NAME', 'tareas_db')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASS = os.getenv('DB_PASS', 'password')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def init_db():
    """Crea la tabla con la columna 'completed' para el check"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Hemos añadido 'completed BOOLEAN DEFAULT FALSE'
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
        logger.info("Base de datos inicializada correctamente con soporte para estados.")
    except Exception as e:
        logger.error(f"No se pudo conectar a la base de datos: {e}")
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tasks', methods=['GET'])
def list_tasks():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Seleccionamos también la columna completed
        cur.execute('SELECT id, content, completed, created_at FROM tasks ORDER BY created_at DESC;')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        logger.error(f"Error obteniendo tareas: {e}")
        return jsonify({"error": "Error interno"}), 500

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Contenido obligatorio"}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('INSERT INTO tasks (content) VALUES (%s) RETURNING *;', (data['content'],))
        new_task = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Tarea creada: {data['content']}")
        return jsonify(new_task), 201
    except Exception as e:
        logger.error(f"Error al guardar: {e}")
        return jsonify({"error": "Error al guardar"}), 500

@app.route('/tasks/<int:task_id>', methods=['PATCH'])
def update_task(task_id):
    """Ruta para marcar como completada o pendiente"""
    data = request.get_json()
    completed = data.get('completed')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE tasks SET completed = %s WHERE id = %s', (completed, task_id))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Tarea {task_id} actualizada a: {completed}")
        return jsonify({"status": "updated"})
    except Exception as e:
        logger.error(f"Error al actualizar tarea {task_id}: {e}")
        return jsonify({"error": "No se pudo actualizar"}), 500

if __name__ == '__main__':
    time.sleep(5)
    init_db()
    app.run(host='0.0.0.0', port=5000)
