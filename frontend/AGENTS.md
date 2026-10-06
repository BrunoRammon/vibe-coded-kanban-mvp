# Frontend Codebase Documentation

This document describes the existing frontend code for the Kanban Board MVP to help agents understand the architecture and current state.

## Stack
- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS with custom CSS variables (`globals.css`)
- **Drag and Drop:** `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- **Testing:** Vitest (Unit/Integration) and Playwright (E2E)

## Structure

- `src/app/page.tsx`: The main entry point, rendering the `<KanbanBoard />` component.
- `src/components/KanbanBoard.tsx`: The main orchestrator for the board. It holds the board state using React `useState` and handles drag-and-drop events via `DndContext`.
- `src/components/KanbanColumn.tsx`: Renders a single column using `useDroppable` and `SortableContext`. Includes inline editing for the column title.
- `src/components/KanbanCard.tsx`: Renders an individual card using `useSortable`. Handles displaying the card title, details, and delete actions.
- `src/components/KanbanCardPreview.tsx`: Renders a dragged card during a drag operation (`DragOverlay`).
- `src/components/NewCardForm.tsx`: Form at the bottom of a column to add a new card.
- `src/lib/kanban.ts`: Contains the types (`Card`, `Column`, `BoardData`), mock data (`initialData`), and logic for moving a card between columns or reordering within a column (`moveCard`).

## State Management
Currently, the state is completely local to the frontend. `KanbanBoard.tsx` initializes its state from `initialData` in `src/lib/kanban.ts`. All changes (move, add, delete, rename) update the React state but are not persisted. 

## Next Steps for the Frontend
1. **Dockerization**: Adapt the Next.js app to be built and served statically by a FastAPI backend inside a Docker container.
2. **Fake Authentication**: Implement a simple dummy login gate ("user", "password") before showing the Kanban board.
3. **API Integration**: Swap out local state for API calls to the FastAPI backend to fetch and mutate the Kanban board state, ensuring persistence.
4. **AI Sidebar**: Integrate a chat interface on the side of the board that communicates with the backend, with the ability to trigger a refresh of the Kanban board when the AI updates it.
