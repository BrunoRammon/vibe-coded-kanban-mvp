# Database Schema (SQLite)

For the MVP, we are using a local SQLite database. To meet the requirements of keeping it simple while supporting future scaling (multiple users, 1 board per user) and storing the board state as JSON, we will use the following schema.

## Tables

### 1. `users`
Stores user accounts. Even though authentication is hardcoded to `"user"` for the MVP, having a users table accommodates future scaling for real authentication.
*   `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
*   `username`: `TEXT UNIQUE NOT NULL`
*   `created_at`: `DATETIME DEFAULT CURRENT_TIMESTAMP`

### 2. `boards`
Stores the Kanban board data. There is a 1-to-1 relationship with the `users` table, and the board state itself is stored entirely as a JSON string to keep the MVP implementation simple.
*   `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
*   `user_id`: `INTEGER UNIQUE NOT NULL` (Foreign key referencing `users(id)`)
*   `data`: `TEXT NOT NULL` (The JSON string representing the board's columns and cards)
*   `updated_at`: `DATETIME DEFAULT CURRENT_TIMESTAMP`

## Example JSON `data` payload
This matches the `BoardData` structure used by the Next.js frontend and FastAPI backend:
```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1"]
    },
    {
      "id": "col-discovery",
      "title": "Discovery",
      "cardIds": []
    },
    {
      "id": "col-progress",
      "title": "In Progress",
      "cardIds": []
    },
    {
      "id": "col-review",
      "title": "Review",
      "cardIds": []
    },
    {
      "id": "col-done",
      "title": "Done",
      "cardIds": []
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    }
  }
}
```

## Initial Setup
When the application starts, if the database is empty, we will automatically insert the hardcoded mock user `(username: "user")` and an initial empty board into the database so the app works immediately out of the box.

