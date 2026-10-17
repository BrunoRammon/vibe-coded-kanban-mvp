import { expect, test, type Locator, type Page } from "@playwright/test";
import { initialData } from "../src/lib/kanban";

async function dragCardToColumn(page: Page, card: Locator, targetColumn: Locator) {
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
}

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[placeholder="user"]', "user");
  await page.fill('input[placeholder="password"]', "password");
  await page.click('button:has-text("Sign In")');
  await page.waitForURL("**/");
  await page.request.put("/api/board", { data: initialData });
});

test("moves a card to an empty column", async ({ page }) => {
  await page.goto("/");

  const discoveryCol = page.getByTestId("column-col-discovery");
  const card3 = page.getByTestId("card-card-3");
  const reviewCol = page.getByTestId("column-col-review");

  await dragCardToColumn(page, card3, reviewCol);

  await expect(discoveryCol.locator('[data-testid^="card-"]')).toHaveCount(0);

  const card1 = page.getByTestId("card-card-1");
  await dragCardToColumn(page, card1, discoveryCol);

  await expect(discoveryCol.getByTestId("card-card-1")).toBeVisible();
});

