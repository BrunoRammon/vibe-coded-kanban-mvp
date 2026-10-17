import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

const getFirstColumn = async () => (await screen.findAllByTestId(/column-/i))[0];

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.spyOn(global, "fetch").mockImplementation(async (_input, init) => {
      if (init?.method === "PUT") {
        return {
          ok: true,
          json: async () => ({ message: "Board updated successfully" }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => structuredClone(initialData),
      } as Response;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders five columns", async () => {
    render(<KanbanBoard />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name{enter}");
    expect(input).toHaveValue("New Name");
  });

  it("adds, edits, and removes a card", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    const editButton = within(column).getByRole("button", {
      name: /edit new card/i,
    });
    await userEvent.click(editButton);

    const editTitleInput = within(column).getByLabelText("Edit card title");
    await userEvent.clear(editTitleInput);
    await userEvent.type(editTitleInput, "Edited card");

    const editDetailsInput = within(column).getByLabelText("Edit card details");
    await userEvent.clear(editDetailsInput);
    await userEvent.type(editDetailsInput, "Updated notes");

    await userEvent.click(within(column).getByRole("button", { name: /save/i }));

    expect(within(column).getByText("Edited card")).toBeInTheDocument();
    expect(within(column).getByText("Updated notes")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete edited card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("Edited card")).not.toBeInTheDocument();
  });
});


