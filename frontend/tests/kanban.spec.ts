import { expect, test } from "@playwright/test";
import { initialData } from "../src/lib/kanban";

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[placeholder="user"]', "user");
  await page.fill('input[placeholder="password"]', "password");
  await page.click('button:has-text("Sign In")');
  await page.waitForURL("**/");
  await page.request.put("/api/board", { data: initialData });
});

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds and edits a card in a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();

  await firstColumn.getByRole("button", { name: "Edit Playwright card", exact: true }).click();
  await firstColumn.getByLabel("Edit card title").fill("Updated Playwright card");
  await firstColumn.getByLabel("Edit card details").fill("Edited via e2e.");
  await firstColumn.getByRole("button", { name: "Save", exact: true }).click();
  await expect(firstColumn.getByText("Updated Playwright card")).toBeVisible();
  await expect(firstColumn.getByText("Edited via e2e.")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("updates the board via AI chat sidebar", async ({ page }) => {
  const updatedBoard = structuredClone(initialData);
  updatedBoard.cards["card-ai"] = {
    id: "card-ai",
    title: "AI Created Task",
    details: "Created by AI assistant",
  };
  updatedBoard.columns[0].cardIds.push("card-ai");

  await page.route("**/api/ai/chat", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        response_message: "I added 'AI Created Task' to Backlog.",
        updated_board: updatedBoard,
      }),
    });
  });

  await page.goto("/");
  await page.locator("button.fixed.bottom-6.right-6").click();
  await expect(page.getByRole("heading", { name: "AI Assistant" })).toBeVisible();

  await page.getByPlaceholder("Ask me to move a card...").fill("Add AI Created Task");
  await page.locator('form button[type="submit"]').click();

  await expect(page.getByText("I added 'AI Created Task' to Backlog.")).toBeVisible();
  await expect(page.getByTestId("column-col-backlog").getByText("AI Created Task")).toBeVisible();
});

