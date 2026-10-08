import pytest
from fastapi.testclient import TestClient
import os
import sqlite3

# Set a test database
os.environ["TEST_DB"] = "1"

# We must mock DB_FILE in database.py before importing main
import backend.database
backend.database.DB_FILE = "backend/test_kanban.db"

from backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Clear cookies
    client.cookies.clear()
    
    # Remove the test db before tests if exists
    if os.path.exists(backend.database.DB_FILE):
        os.remove(backend.database.DB_FILE)
    
    # Initialize the database (this will create tables and seed 'user')
    backend.database.init_db()
    
    yield
    
    # Clean up after
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
    
    # Fetch existing board
    res1 = client.get("/api/board")
    board = res1.json()
    
    # Modify the title of the first column
    board["columns"][0]["title"] = "Modified To Do"
    
    # Update the board
    res2 = client.put("/api/board", json=board)
    assert res2.status_code == 200
    assert res2.json() == {"message": "Board updated successfully"}
    
    # Fetch again to verify persistence
    res3 = client.get("/api/board")
    updated_board = res3.json()
    assert updated_board["columns"][0]["title"] == "Modified To Do"

from unittest.mock import patch, MagicMock

def test_ai_test_unauthenticated():
    response = client.get("/api/ai/test")
    assert response.status_code == 401

@patch("backend.main.OpenAI")
def test_ai_test_authenticated(mock_openai):
    # Mock the OpenAI response
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "4"
    mock_client.chat.completions.create.return_value = mock_response
    
    # Authenticate and set env var
    client.cookies.set("session", "fake-session-token")
    os.environ["OPENROUTER_API_KEY"] = "fake-key"
    
    response = client.get("/api/ai/test")
    
    assert response.status_code == 200
    assert response.json() == {"response": "4"}
    
    mock_client.chat.completions.create.assert_called_once()

@patch("backend.main.OpenAI")
def test_ai_chat_updates_board(mock_openai):
    # Setup mock to return a new board state
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"response_message": "Added task", "updated_board": {"columns": [], "cards": [{"id": "1", "title": "New Task", "columnId": "col-todo"}]}}'
    mock_client.chat.completions.create.return_value = mock_response
    
    client.cookies.set("session", "fake-session-token")
    os.environ["OPENROUTER_API_KEY"] = "fake-key"
    
    # We need to make sure the user has a board before we chat, which init_db already provides.
    response = client.post("/api/ai/chat", json={"message": "Add a task"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["response_message"] == "Added task"
    assert data["updated_board"]["cards"][0]["title"] == "New Task"
    
    # Verify the DB was actually updated
    board_res = client.get("/api/board")
    assert board_res.json()["cards"][0]["title"] == "New Task"

@patch("backend.main.OpenAI")
def test_ai_chat_no_update(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"response_message": "Hello!", "updated_board": null}'
    mock_client.chat.completions.create.return_value = mock_response
    
    client.cookies.set("session", "fake-session-token")
    os.environ["OPENROUTER_API_KEY"] = "fake-key"
    
    response = client.post("/api/ai/chat", json={"message": "Hi"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["response_message"] == "Hello!"
    assert data["updated_board"] is None
