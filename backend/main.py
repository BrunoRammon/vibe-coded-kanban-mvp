import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Response, Cookie, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Kanban Board API")

# Ensure the static directory exists so FastAPI doesn't crash on startup
os.makedirs("backend/static", exist_ok=True)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest, response: Response):
    if req.username == "user" and req.password == "password":
        response.set_cookie(key="session", value="fake-session-token", httponly=True, samesite="lax")
        return {"message": "Logged in successfully"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(key="session")
    return {"message": "Logged out successfully"}

@app.get("/api/me")
def get_me(session: Optional[str] = Cookie(None)):
    if session == "fake-session-token":
        return {"username": "user"}
    raise HTTPException(status_code=401, detail="Not authenticated")

# Health check endpoint
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

from backend.database import init_db, get_user_id_by_username, get_board_for_user, update_board_for_user

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/api/board")
def get_board(response: Response, session: Optional[str] = Cookie(None)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    
    if session != "fake-session-token":
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # We only have "user" for MVP
    user_id = get_user_id_by_username("user")
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
        
    board = get_board_for_user(user_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
        
    return board

@app.put("/api/board")
def update_board(board_data: dict, session: Optional[str] = Cookie(None)):
    if session != "fake-session-token":
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    user_id = get_user_id_by_username("user")
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
        
    update_board_for_user(user_id, board_data)
    return {"message": "Board updated successfully"}

# API routes should be defined above this point.

from openai import OpenAI
import os

@app.get("/api/ai/test")
def ai_test(session: Optional[str] = Cookie(None)):
    if session != "fake-session-token":
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": "What is 2+2? Answer simply."}
            ]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str

@app.post("/api/ai/chat")
def ai_chat(req: ChatRequest, session: Optional[str] = Cookie(None)):
    if session != "fake-session-token":
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    user_id = get_user_id_by_username("user")
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
        
    board = get_board_for_user(user_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
        
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    import json
    
    system_prompt = f"""You are an AI assistant helping a user manage their Kanban board.
The current board state is:
{json.dumps(board)}

You must respond in JSON format with exactly two keys:
1. "response_message": A string containing a helpful message to the user about what you did or answering their question.
2. "updated_board": If you need to make changes to the board, provide the entirely new board JSON object here. If no changes are needed, this should be null.

Do NOT wrap the JSON in Markdown backticks (e.g., no ```json). Just output raw JSON.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if the model still wrapped in markdown
            if content.startswith("```json"):
                content = content[7:-3].strip()
                parsed = json.loads(content)
            else:
                raise ValueError("Could not parse JSON from AI response")
                
        # If the AI provided an updated board, save it
        if parsed.get("updated_board"):
            update_board_for_user(user_id, parsed["updated_board"])
            
        return {
            "response_message": parsed.get("response_message", "I have updated the board."),
            "updated_board": parsed.get("updated_board")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import FileResponse
import os

@app.get("/{full_path:path}")
async def serve_static_or_html(full_path: str):
    # If path is empty, serve index.html
    if not full_path or full_path == "/":
        return FileResponse("backend/static/index.html")
        
    # Check if the exact file exists (for CSS, JS, etc.)
    static_file_path = f"backend/static/{full_path}"
    if os.path.isfile(static_file_path):
        return FileResponse(static_file_path)
        
    # Check if an .html version exists (for Next.js routes like /login -> login.html)
    html_path = f"backend/static/{full_path}.html"
    if os.path.isfile(html_path):
        return FileResponse(html_path)
        
    # Check if a directory exists with an index.html
    index_path = f"backend/static/{full_path}/index.html"
    if os.path.isfile(index_path):
        return FileResponse(index_path)
        
    # Fallback to index.html for client-side routing, or return 404
    # In Next.js with App Router, static export produces individual HTML files.
    # If it's not found, we can return the 404.html generated by Next.js
    not_found_path = "backend/static/404.html"
    if os.path.isfile(not_found_path):
        return FileResponse(not_found_path, status_code=404)
        
    raise HTTPException(status_code=404, detail="Not found")
