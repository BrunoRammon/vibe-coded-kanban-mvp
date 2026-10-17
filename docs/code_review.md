# Code Review Report

## Executive Summary

The Project Management MVP application is functional end-to-end: the Next.js static export is built and served by FastAPI inside Docker, authentication gates access to the board, board state persists to SQLite, and the OpenRouter AI chat sidebar can read and update the board. All automated tests (8 backend `pytest` tests, 6 frontend `vitest` unit tests, and 8 `playwright` E2E tests) pass.

However, the review identified one missing business requirement from `AGENTS.md` (editing existing cards in the UI), several security and validation gaps in the backend, minor frontend and Docker inefficiencies, stray scratch files in the working tree, and outdated documentation.

---

## Findings and Recommended Actions

### 1. Business Requirements

#### [HIGH] Missing UI ability to edit existing cards
- **Location:** [`frontend/src/components/KanbanCard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanCard.tsx), [`frontend/src/components/KanbanBoard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx)
- **Issue:** [`AGENTS.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/AGENTS.md) specifies: *"The cards on the Kanban board can be moved with drag and drop, and edited"*. Currently, columns can be renamed inline and cards can be created, dragged, or deleted, or modified via AI chat, but there is no UI control on [`KanbanCard`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanCard.tsx#L11-L53) to edit a card's title or details directly.
- **Action:** Add a simple inline edit mode to [`KanbanCard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanCard.tsx) and wire it to an `handleEditCard(cardId, title, details)` callback in [`KanbanBoard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx) that calls `syncBoard`.

---

### 2. Backend Security, Validation, and Idioms

#### [HIGH] Path traversal risk in static file catch-all route
- **Location:** [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py#L181-L209)
- **Issue:** `serve_static_or_html` constructs file paths via string interpolation (`f"backend/static/{full_path}"`) without verifying that the resolved path stays inside `backend/static`. Crafted requests or symlinks could potentially read files outside the static directory.
- **Action:** Resolve paths with `pathlib.Path("backend/static").resolve()` and verify `candidate.is_relative_to(static_root)` before returning `FileResponse`.

#### [HIGH] Unvalidated board schema in `PUT /api/board` and `/api/ai/chat`
- **Location:** [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py#L65-L75), [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py#L110-L175)
- **Issue:**
  1. `update_board` accepts an arbitrary `dict` (`board_data: dict`) without validating that `columns` and `cards` match the schema expected by the frontend (`BoardData`).
  2. `ai_chat` prompts the model with `response_format={"type": "json_object"}` and writes `parsed["updated_board"]` directly to SQLite without schema validation. If the LLM returns `cards` as a list instead of a `Record<string, Card>` map (which even occurs in the mock payload in [`backend/test_api.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/test_api.py#L105)), the frontend crashes when rendering `column.cardIds.map((cardId) => board.cards[cardId])`.
- **Action:** Define Pydantic models (`CardModel`, `ColumnModel`, `BoardDataModel`, `AiChatResponse`) in [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py), use `BoardDataModel` as the request body type for `PUT /api/board`, validate `updated_board` with `BoardDataModel` in `/api/ai/chat`, and update the mock payload in [`backend/test_api.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/test_api.py#L105) to match the real board schema.

#### [MEDIUM] Deprecated `@app.on_event("startup")`, duplicated auth checks, and scattered imports
- **Location:** [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py#L1-L180)
- **Issue:**
  1. `@app.on_event("startup")` (line 43) is deprecated in FastAPI and emits `DeprecationWarning` on every test run.
  2. Module imports (`os`, `json`, `OpenAI`, `FileResponse`, ` backend.database`) are scattered throughout the file (lines 1, 41, 79, 80, 132, 178, 179).
  3. Cookie verification (`session != "fake-session-token"`) and user lookup (`get_user_id_by_username("user")`) are repeated across 5 endpoints even though `Depends` is imported on line 4.
- **Action:**
  1. Replace `@app.on_event("startup")` with an `asynccontextmanager` `lifespan` handler on `FastAPI(lifespan=lifespan)`.
  2. Consolidate all imports at the top of [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py).
  3. Extract `require_auth` / `get_current_user_id` dependencies using `Depends`.

---

### 3. Frontend Architecture and UX

#### [MEDIUM] `PUT /api/board` fires on every keystroke when renaming a column
- **Location:** [`frontend/src/components/KanbanColumn.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanColumn.tsx#L42-L47), [`frontend/src/components/KanbanBoard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx#L71-L80)
- **Issue:** Typing a new column title triggers `onChange` -> `handleRenameColumn` -> `syncBoard` on every character typed, sending a full board `PUT /api/board` request per keystroke.
- **Action:** Update local React state on `onChange` and persist via `PUT /api/board` on `onBlur` (or debounce network persistence), or maintain local draft input state in `KanbanColumn` and commit on blur/Enter.

#### [LOW] Potential `undefined` card rendering if `cardIds` and `cards` drift
- **Location:** [`frontend/src/components/KanbanBoard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx#L182)
- **Issue:** `column.cardIds.map((cardId) => board.cards[cardId])` assumes every ID in `column.cardIds` exists in `board.cards`. If an AI update produces a dangling `cardId`, `KanbanCard` receives `undefined` and throws a runtime error.
- **Action:** Filter resolved cards with `.filter((card): card is Card => Boolean(card))`.

---

### 4. Docker and Scripts

#### [MEDIUM] Redundant package installation on every container start
- **Location:** [`docker-compose.yml`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docker-compose.yml#L13)
- **Issue:** `docker-compose.yml` overrides `command` to run `uv pip install --system -r /app/backend/requirements.txt` before starting `uvicorn`, even though [`Dockerfile`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/Dockerfile#L23) already installs all dependencies at build time. This slows down container startup by 25–30 seconds and requires network access on container start.
- **Action:** Simplify `command` in [`docker-compose.yml`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docker-compose.yml) to `uvicorn backend.main:app --host 0.0.0.0 --port 8000` (matching `Dockerfile`).

#### [LOW] Incomplete `.dockerignore`
- **Location:** [`.dockerignore`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/.dockerignore)
- **Issue:** `.env`, `backend/*.db`, `frontend/out`, and `frontend/test-results` are not listed in `.dockerignore`, allowing local database files, test artifacts, and secrets to be sent into the Docker build context.
- **Action:** Add `.env`, `backend/*.db`, `frontend/out`, `frontend/test-results`, and `frontend/playwright-report` to [`.dockerignore`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/.dockerignore).

---

### 5. Repository Hygiene and Test Layout

#### [MEDIUM] Stray scratch scripts and patch/backup files in the repository
- **Location:**
  - [`patch_board.patch`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/patch_board.patch), [`revert.patch`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/revert.patch), [`test_api_real.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/test_api_real.py)
  - [`backend/test_headers.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/test_headers.py), [`backend/test_openrouter.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/test_openrouter.py), [`backend/test_real.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/test_real.py)
  - [`frontend/src/components/KanbanBoard.tsx.orig`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx.orig), [`frontend/src/components/KanbanBoard.tsx.patch`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx.patch), [`frontend/tests/test_empty_col_console.ts`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/tests/test_empty_col_console.ts)
- **Issue:**
  1. Several one-off debugging scripts and patch/backup files were left in the repo.
  2. Because `backend/test_headers.py`, `backend/test_openrouter.py`, `backend/test_real.py`, and `test_api_real.py` match `pytest`'s `test_*.py` discovery pattern and execute live HTTP requests at import time, running `pytest` without explicit file arguments fails during test collection.
  3. [`scripts/test.sh`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/scripts/test.sh) runs `pytest backend/tests/`, which only runs `test_main.py` (1 test) and skips [`backend/test_api.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/test_api.py) (7 tests).
- **Action:**
  1. Delete the stray `.patch`, `.orig`, and ad-hoc script files (`patch_board.patch`, `revert.patch`, `test_api_real.py`, `backend/test_headers.py`, `backend/test_openrouter.py`, `backend/test_real.py`, `frontend/src/components/KanbanBoard.tsx.orig`, `frontend/src/components/KanbanBoard.tsx.patch`, `frontend/tests/test_empty_col_console.ts`).
  2. Move [`backend/test_api.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/test_api.py) to `backend/tests/test_api.py` so [`scripts/test.sh`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/scripts/test.sh) and plain `pytest` execute the full backend suite.

---

### 6. Documentation Accuracy

#### [LOW] Outdated schema and frontend documentation
- **Location:** [`docs/DB_SCHEMA.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/DB_SCHEMA.md), [`frontend/AGENTS.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/AGENTS.md), [`docs/PLAN.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/PLAN.md)
- **Issue:**
  1. [`docs/DB_SCHEMA.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/DB_SCHEMA.md#L20-L46) shows the board `data` payload as a JSON list of columns with embedded `cards` arrays (`description` field), whereas [`backend/database.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/database.py#L9-L27) and [`frontend/src/lib/kanban.ts`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/lib/kanban.ts#L13-L72) use `{ "columns": [{ "id", "title", "cardIds" }], "cards": { "<id>": { "id", "title", "details" } } }`.
  2. [`frontend/AGENTS.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/AGENTS.md#L22-L29) still describes state as purely local and lists completed features (Dockerization, Fake Auth, API Integration, AI Sidebar) under "Next Steps".
  3. [`docs/PLAN.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/PLAN.md#L6) still has `- [ ] Ensure the user checks and approves the plan.` unchecked even though Parts 1–10 are complete.
- **Action:** Update [`docs/DB_SCHEMA.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/DB_SCHEMA.md), [`frontend/AGENTS.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/AGENTS.md), and [`docs/PLAN.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/PLAN.md) to reflect the implemented architecture.

---

## Action Checklist

- [x] **Action 1 (High):** Add card editing UI in [`frontend/src/components/KanbanCard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanCard.tsx) and [`frontend/src/components/KanbanBoard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx) with unit/E2E test coverage.
- [x] **Action 2 (High):** Harden static file serving against path traversal in [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py).
- [x] **Action 3 (High):** Add Pydantic schema validation (`BoardDataModel`) for `PUT /api/board` and `/api/ai/chat` responses in [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py).
- [x] **Action 4 (Medium):** Refactor [`backend/main.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/main.py) to use FastAPI `lifespan`, top-level imports, and `Depends` for authentication.
- [x] **Action 5 (Medium):** Clean up stray scratch/patch files and move [`backend/test_api.py`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/backend/tests/test_api.py) into `backend/tests/test_api.py`.
- [x] **Action 6 (Medium):** Remove redundant `uv pip install` on startup in [`docker-compose.yml`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docker-compose.yml) and update [`.dockerignore`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/.dockerignore).
- [x] **Action 7 (Medium):** Persist column title edits on blur (instead of every keystroke) and guard against missing card IDs in [`frontend/src/components/KanbanColumn.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanColumn.tsx) and [`frontend/src/components/KanbanBoard.tsx`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/src/components/KanbanBoard.tsx).
- [x] **Action 8 (Low):** Update [`docs/DB_SCHEMA.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/DB_SCHEMA.md), [`frontend/AGENTS.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/frontend/AGENTS.md), and [`docs/PLAN.md`](file:///home/bruno/Documents/Programming/Cursos/udemy/ed_donner_ai/pm/docs/PLAN.md) to match the current codebase.
