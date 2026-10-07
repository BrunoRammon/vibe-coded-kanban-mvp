import sqlite3
import json
import os
from contextlib import contextmanager

DB_FILE = "backend/kanban.db"

# Default initial board data matching the frontend
INITIAL_BOARD_DATA = [
    {
        "id": "todo",
        "title": "To Do",
        "cards": [
            {
                "id": "card-1",
                "title": "Setup project repository",
                "description": "Initialize NextJS and FastAPI"
            }
        ]
    },
    {
        "id": "in-progress",
        "title": "In Progress",
        "cards": []
    },
    {
        "id": "done",
        "title": "Done",
        "cards": []
    }
]

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create boards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                data TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Seed default user if empty
        cursor.execute("SELECT id FROM users WHERE username = 'user'")
        user = cursor.fetchone()
        
        if not user:
            cursor.execute("INSERT INTO users (username) VALUES ('user')")
            user_id = cursor.lastrowid
            
            # Seed initial board for default user
            cursor.execute(
                "INSERT INTO boards (user_id, data) VALUES (?, ?)",
                (user_id, json.dumps(INITIAL_BOARD_DATA))
            )
        
        conn.commit()

def get_user_id_by_username(username: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row["id"] if row else None

def get_board_for_user(user_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM boards WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row["data"])
        return None

def update_board_for_user(user_id: int, data: list):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE boards SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (json.dumps(data), user_id)
        )
        conn.commit()

