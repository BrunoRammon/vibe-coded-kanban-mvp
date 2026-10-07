import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[placeholder="user"]', "user");
  await page.fill('input[placeholder="password"]', "password");
  await page.click('button:has-text("Sign In")');
  await page.waitForURL("**/");
});

test("moves a card to an empty column logs", async ({ page }) => {
  page.on("console", (msg) => {
    console.log(`BROWSER CONSOLE: ${msg.text()}`);
  });
  
  await page.goto("/");
  
  const discoveryCol = page.getByTestId("column-col-discovery");
  const card3 = page.getByTestId("card-card-3");
  const reviewCol = page.getByTestId("column-col-review");
  await card3.dragTo(reviewCol);
  
  await expect(discoveryCol.locator('[data-testid^="card-"]')).toHaveCount(0);
  
  const card1 = page.getByTestId("card-card-1");
  await card1.dragTo(discoveryCol);
  
  await expect(discoveryCol.getByTestId("card-card-1")).toBeVisible();
});
