# Frontend Codebase Documentation

This document describes the existing frontend code for the Kanban Board MVP to help agents understand the architecture and current state.

## Stack
- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS with custom CSS variables (`globals.css`)
- **Drag and Drop:** `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- **Testing:** Vitest (Unit/Integration) and Playwright (E2E)

## Structure

- `src/app/page.tsx`: The main authenticated entry point. Verifies the user session via `GET /api/me`, redirects unauthenticated users to `/login`, provides a logout button (`POST /api/logout`), and renders `<KanbanBoard />`.
- `src/app/login/page.tsx`: Login page UI that authenticates via `POST /api/login`.
- `src/components/KanbanBoard.tsx`: The main orchestrator for the board. Fetches initial state from `GET /api/board`, syncs mutations via `PUT /api/board`, handles drag-and-drop events via `DndContext`, and renders `<AiSidebar />`.
- `src/components/KanbanColumn.tsx`: Renders a single column using `useDroppable` and `SortableContext`. Includes inline editing for the column title (committed on blur or Enter).
- `src/components/KanbanCard.tsx`: Renders an individual card using `useSortable`. Supports inline editing of the card title and details, as well as card deletion.
- `src/components/KanbanCardPreview.tsx`: Renders a dragged card during a drag operation (`DragOverlay`).
- `src/components/NewCardForm.tsx`: Form at the bottom of a column to add a new card.
- `src/components/AiSidebar.tsx`: Floating chat widget that sends natural language requests to `POST /api/ai/chat` and updates the board state when the AI modifies the board.
- `src/lib/kanban.ts`: Contains the types (`Card`, `Column`, `BoardData`), seed data (`initialData`), and logic for moving a card between columns or reordering within a column (`moveCard`).

## State Management & Build
`KanbanBoard.tsx` loads board state from the FastAPI backend (`GET /api/board`) and persists changes (`PUT /api/board`) on column rename, card creation, card edit, card deletion, and drag-and-drop. The Next.js app is configured with `output: "export"` in `next.config.ts` and is served statically by FastAPI in Docker.

