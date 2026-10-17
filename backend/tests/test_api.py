import json
import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

import backend.database

backend.database.DB_FILE = "backend/test_kanban.db"

from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    client.cookies.clear()

    if os.path.exists(backend.database.DB_FILE):
        os.remove(backend.database.DB_FILE)

    backend.database.init_db()

    yield

    if os.path.exists(backend.database.DB_FILE):
        os.remove(backend.database.DB_FILE)


def test_get_board_unauthenticated():
    response = client.get("/api/board")
    assert response.status_code == 401


def test_get_board_authenticated():
    client.cookies.set("session", "fake-session-token")
    response = client.get("/api/board")
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "cards" in data
    assert data["columns"][0]["id"] == "col-backlog"


def test_update_board():
    client.cookies.set("session", "fake-session-token")

    res1 = client.get("/api/board")
    board = res1.json()

    board["columns"][0]["title"] = "Modified To Do"

    res2 = client.put("/api/board", json=board)
    assert res2.status_code == 200
    assert res2.json() == {"message": "Board updated successfully"}

    res3 = client.get("/api/board")
    updated_board = res3.json()
    assert updated_board["columns"][0]["title"] == "Modified To Do"


def test_update_board_invalid_schema():
    client.cookies.set("session", "fake-session-token")
    res = client.put("/api/board", json={"columns": "not-a-list"})
    assert res.status_code == 422


def test_ai_test_unauthenticated():
    response = client.get("/api/ai/test")
    assert response.status_code == 401


@patch("backend.main.OpenAI")
def test_ai_test_authenticated(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "4"
    mock_client.chat.completions.create.return_value = mock_response

    client.cookies.set("session", "fake-session-token")
    os.environ["OPENROUTER_API_KEY"] = "fake-key"

    response = client.get("/api/ai/test")

    assert response.status_code == 200
    assert response.json() == {"response": "4"}
    mock_client.chat.completions.create.assert_called_once()


@patch("backend.main.OpenAI")
def test_ai_chat_updates_board(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    updated_board_payload = {
        "columns": [{"id": "col-todo", "title": "To Do", "cardIds": ["1"]}],
        "cards": {
            "1": {
                "id": "1",
                "title": "New Task",
                "details": "Created by AI",
            }
        },
    }

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "response_message": "Added task",
            "updated_board": updated_board_payload,
        }
    )
    mock_client.chat.completions.create.return_value = mock_response

    client.cookies.set("session", "fake-session-token")
    os.environ["OPENROUTER_API_KEY"] = "fake-key"

    response = client.post("/api/ai/chat", json={"message": "Add a task"})

    assert response.status_code == 200
    data = response.json()
    assert data["response_message"] == "Added task"
    assert data["updated_board"]["cards"]["1"]["title"] == "New Task"

    board_res = client.get("/api/board")
    assert board_res.json()["cards"]["1"]["title"] == "New Task"


@patch("backend.main.OpenAI")
def test_ai_chat_no_update(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        '{"response_message": "Hello!", "updated_board": null}'
    )
    mock_client.chat.completions.create.return_value = mock_response

    client.cookies.set("session", "fake-session-token")
    os.environ["OPENROUTER_API_KEY"] = "fake-key"

    response = client.post("/api/ai/chat", json={"message": "Hi"})

    assert response.status_code == 200
    data = response.json()
    assert data["response_message"] == "Hello!"
    assert data["updated_board"] is None
