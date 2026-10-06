# Detailed Project Plan

## Part 1: Plan
- [x] Enrich this document to plan out each of these parts in detail, with substeps listed out as a checklist to be checked off by the agent, and with tests and success criteria for each.
- [x] Create an `AGENTS.md` file inside the `frontend` directory that describes the existing code there.
- [ ] Ensure the user checks and approves the plan.
**Success Criteria:** `docs/PLAN.md` contains detailed checklists and testing criteria, `frontend/AGENTS.md` exists and accurately describes the frontend, and the user approves the plan.

## Part 2: Scaffolding
- [ ] Create a `backend/` directory and initialize a FastAPI application.
- [ ] Create `Dockerfile` and `docker-compose.yml` (if needed) for the full stack.
- [ ] Configure `uv` as the package manager in the Docker container for Python.
- [ ] Write `scripts/start.sh`, `scripts/stop.sh` (and `.bat` equivalents for Windows if requested) to manage the container.
- [ ] Setup FastAPI to serve a basic "Hello World" static HTML at `/` and a `/api/health` endpoint.
- [ ] **Tests:**
  - Automated: `pytest` verifying the `/api/health` endpoint.
  - Manual: Run the start script, verify `http://localhost:8000` shows "Hello World", and `/api/health` returns OK.
**Success Criteria:** Docker environment runs successfully, Python dependencies are managed with `uv`, and start/stop scripts work flawlessly.

## Part 3: Add in Frontend
- [ ] Update the `Next.js` configuration in `frontend/` to support static export (`output: 'export'`).
- [ ] Adjust the Dockerfile to build the Next.js static site and copy it into the FastAPI static files directory.
- [ ] Update FastAPI to serve the Next.js static files at `/`.
- [ ] **Tests:**
  - Automated: Ensure Vitest unit tests in `frontend/` pass.
  - Manual: Build and start the Docker container. Open `http://localhost:8000` and verify the Kanban board MVP UI is displayed.
**Success Criteria:** The Kanban UI is served perfectly from the FastAPI backend without needing a separate Next.js dev server.

## Part 4: Add in a fake user sign in experience
- [ ] Create a simple login page UI component in Next.js.
- [ ] Implement a session/cookie-based dummy authentication mechanism on the frontend/backend.
- [ ] Protect the Kanban board route so it redirects to `/login` if not authenticated.
- [ ] Hardcode the allowed credentials to "user" and "password".
- [ ] Implement a logout functionality.
- [ ] **Tests:**
  - Automated: Playwright E2E tests verifying login failure, login success, and logout.
  - Manual: Open app -> see login -> enter bad creds (fail) -> enter user/password (success) -> see board -> click logout -> return to login.
**Success Criteria:** Users cannot see the board without signing in with "user" / "password".

## Part 5: Database modeling
- [ ] Propose an SQLite schema design to store the Kanban board as JSON (to match the MVP limitations). The schema should accommodate multiple users (for future scaling) and 1 Kanban board per user.
- [ ] Document the proposed schema in `docs/DB_SCHEMA.md`.
- [ ] Get user sign off on the database approach.
- [ ] **Tests:**
  - Manual: User reviews and approves `DB_SCHEMA.md`.
**Success Criteria:** A solid, documented plan for the SQLite schema that fulfills MVP needs.

## Part 6: Backend DB and API
- [ ] Set up SQLite integration in FastAPI. The DB file should be created automatically if it doesn't exist.
- [ ] Create CRUD endpoints: `GET /api/board`, `POST /api/board` (or PUT for updates).
- [ ] Link these routes to the logged-in user.
- [ ] **Tests:**
  - Automated: `pytest` to test DB creation, inserting board data, and retrieving board data for a mock user.
  - Manual: Use cURL or Swagger UI (`/docs`) to test fetching and updating board data.
**Success Criteria:** The backend can successfully persist and retrieve JSON board data to/from SQLite.

## Part 7: Frontend + Backend Integration
- [ ] Replace `initialData` in the frontend with a fetch call to `GET /api/board` on load.
- [ ] Modify the drag-and-drop, add, edit, and delete handlers to persist changes via API calls (`POST / PUT /api/board`).
- [ ] Implement loading states and simple error handling for network failures.
- [ ] **Tests:**
  - Automated: Playwright E2E test dragging a card and verifying persistence.
  - Manual: Log in, move a card, rename a column, refresh the page. Ensure changes persisted.
**Success Criteria:** The Kanban board is fully persistent and functional, seamlessly communicating with the FastAPI backend.

## Part 8: AI connectivity
- [ ] Add OpenRouter API key management via `.env`.
- [ ] Create an endpoint `/api/ai/test` that makes a simple "2+2" prompt to OpenRouter (`openai/gpt-oss-120b`).
- [ ] **Tests:**
  - Automated: Backend mock test for OpenRouter client.
  - Manual: Call `/api/ai/test` and verify a sensible response comes back.
**Success Criteria:** FastAPI backend successfully authenticates and communicates with the OpenRouter API.

## Part 9: AI Kanban Logic
- [ ] Create a new endpoint `/api/ai/chat` that takes the user's message.
- [ ] In the endpoint, gather the user's current Kanban board JSON state from the DB and append it to the context.
- [ ] Instruct the AI to use Structured Outputs to return a response message and optionally a new board state.
- [ ] If the AI returns a new board state, update the DB.
- [ ] **Tests:**
  - Automated: `pytest` testing the `/api/ai/chat` endpoint with mocked AI responses to ensure DB is updated when requested.
  - Manual: Send a prompt like "Add a card for 'Write Docs' to the Backlog" via Swagger UI and verify the DB updates.
**Success Criteria:** The backend handles the heavy lifting of prompting the AI with context, interpreting Structured Outputs, and updating the database.

## Part 10: AI Sidebar Widget UI
- [ ] Design and implement a chat sidebar component in Next.js.
- [ ] Connect the sidebar to the `/api/ai/chat` endpoint.
- [ ] Implement a mechanism for the UI to automatically refresh the board state if the AI made changes to it (e.g., polling, or simply returning the updated board in the chat response and updating React state).
- [ ] **Tests:**
  - Automated: Playwright E2E test chatting with a mocked AI response and verifying the board updates.
  - Manual: Open the app, chat with the AI ("Move 'Task A' to Done"), see the AI reply, and visually confirm the card moved on the board.
**Success Criteria:** A beautiful, intuitive chat interface that empowers the user to manage their Kanban board via natural language.