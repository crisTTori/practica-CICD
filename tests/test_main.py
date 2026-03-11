from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from main import app  # noqa: E402


def test_index_returns_html():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200


@patch("main.get_db_connection")
def test_list_tasks_returns_data(mock_get_db_connection):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.fetchall.return_value = [
        {
            "id": 1,
            "content": "Aprender CI/CD",
            "completed": False,
            "created_at": "2026-03-10 10:00:00"
        }
    ]
    mock_conn.cursor.return_value = mock_cur
    mock_get_db_connection.return_value = mock_conn

    client = app.test_client()
    response = client.get("/tasks")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["content"] == "Aprender CI/CD"


@patch("main.get_db_connection")
def test_add_task_creates_task(mock_get_db_connection):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_cur.fetchone.return_value = {
        "id": 1,
        "content": "Hacer práctica",
        "completed": False,
        "created_at": "2026-03-10 10:00:00"
    }
    mock_conn.cursor.return_value = mock_cur
    mock_get_db_connection.return_value = mock_conn

    client = app.test_client()
    response = client.post("/tasks", json={"content": "Hacer práctica"})

    assert response.status_code == 201
    data = response.get_json()
    assert data["content"] == "Hacer práctica"


def test_add_task_without_content_returns_400():
    client = app.test_client()
    response = client.post("/tasks", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Contenido obligatorio"


@patch("main.get_db_connection")
def test_update_task_returns_updated(mock_get_db_connection):
    mock_conn = MagicMock()
    mock_cur = MagicMock()

    mock_conn.cursor.return_value = mock_cur
    mock_get_db_connection.return_value = mock_conn

    client = app.test_client()
    response = client.patch("/tasks/1", json={"completed": True})

    assert response.status_code == 200
    assert response.get_json()["status"] == "updated"


def test_update_task_without_completed_returns_400():
    client = app.test_client()
    response = client.patch("/tasks/1", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Campo completed obligatorio"
