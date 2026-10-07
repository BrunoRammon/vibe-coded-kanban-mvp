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

