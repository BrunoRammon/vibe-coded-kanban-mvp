from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel

from backend.database import (
    get_board_for_user,
    get_user_id_by_username,
    init_db,
    update_board_for_user,
)

load_dotenv()

STATIC_DIR = Path("backend/static").resolve()
STATIC_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Kanban Board API", lifespan=lifespan)


class LoginRequest(BaseModel):
    username: str
    password: str


class CardModel(BaseModel):
    id: str
    title: str
    details: str


class ColumnModel(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardDataModel(BaseModel):
    columns: list[ColumnModel]
    cards: dict[str, CardModel]


class ChatRequest(BaseModel):
    message: str


class AiChatResponse(BaseModel):
    response_message: str
    updated_board: Optional[BoardDataModel] = None


def require_auth(session: Optional[str] = Cookie(None)) -> str:
    if session != "fake-session-token":
        raise HTTPException(status_code=401, detail="Not authenticated")
    return "user"


def get_current_user_id(username: str = Depends(require_auth)) -> int:
    user_id = get_user_id_by_username(username)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return user_id


@app.post("/api/login")
def login(req: LoginRequest, response: Response):
    if req.username == "user" and req.password == "password":
        response.set_cookie(
            key="session",
            value="fake-session-token",
            httponly=True,
            samesite="lax",
        )
        return {"message": "Logged in successfully"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(key="session")
    return {"message": "Logged out successfully"}


@app.get("/api/me")
def get_me(username: str = Depends(require_auth)):
    return {"username": username}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/board")
def get_board(response: Response, user_id: int = Depends(get_current_user_id)):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    board = get_board_for_user(user_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@app.put("/api/board")
def update_board(
    board_data: BoardDataModel,
    user_id: int = Depends(get_current_user_id),
):
    update_board_for_user(user_id, board_data.model_dump())
    return {"message": "Board updated successfully"}


@app.get("/api/ai/test")
def ai_test(_username: str = Depends(require_auth)):
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
            ],
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/chat")
def ai_chat(req: ChatRequest, user_id: int = Depends(get_current_user_id)):
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

    system_prompt = f"""You are an AI assistant helping a user manage their Kanban board.
The current board state is:
{json.dumps(board)}

You must respond in JSON format with exactly two keys:
1. "response_message": A string containing a helpful message to the user about what you did or answering their question.
2. "updated_board": If you need to make changes to the board, provide the entirely new board JSON object here (matching the exact schema of "columns" and "cards"). If no changes are needed, this should be null.

Do NOT wrap the JSON in Markdown backticks (e.g., no ```json). Just output raw JSON.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or ""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            if content.startswith("```json"):
                content = content[7:-3].strip()
                parsed = json.loads(content)
            else:
                raise ValueError("Could not parse JSON from AI response")

        validated = AiChatResponse.model_validate(parsed)

        if validated.updated_board is not None:
            board_dict = validated.updated_board.model_dump()
            update_board_for_user(user_id, board_dict)
        else:
            board_dict = None

        return {
            "response_message": validated.response_message,
            "updated_board": board_dict,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_static_path(relative_path: str) -> Optional[Path]:
    candidate = (STATIC_DIR / relative_path).resolve()
    if not candidate.is_relative_to(STATIC_DIR):
        return None
    if candidate.is_file():
        return candidate
    return None


@app.get("/{full_path:path}")
async def serve_static_or_html(full_path: str):
    if not full_path or full_path == "/":
        index_file = _resolve_static_path("index.html")
        if index_file:
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not found")

    for candidate_rel in (
        full_path,
        f"{full_path}.html",
        f"{full_path}/index.html",
    ):
        resolved = _resolve_static_path(candidate_rel)
        if resolved:
            return FileResponse(resolved)

    not_found_file = _resolve_static_path("404.html")
    if not_found_file:
        return FileResponse(not_found_file, status_code=404)

    raise HTTPException(status_code=404, detail="Not found")

