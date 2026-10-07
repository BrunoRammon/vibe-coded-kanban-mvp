import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
  await page.fill('input[placeholder="user"]', "user");
  await page.fill('input[placeholder="password"]', "password");
  await page.click('button:has-text("Sign In")');
  await page.waitForURL("**/");
});

test("moves a card to an empty column", async ({ page }) => {
  await page.goto("/");
  
  // First, empty out col-discovery by deleting any cards it might have
  // (In our default data, Discovery has "card-3")
  const discoveryCol = page.getByTestId("column-col-discovery");
  
  // For the sake of the test, let's just move card-3 to Review to make Discovery empty
  const card3 = page.getByTestId("card-card-3");
  const reviewCol = page.getByTestId("column-col-review");
  await card3.dragTo(reviewCol);
  
  // Verify Discovery is empty
  await expect(discoveryCol.locator('[data-testid^="card-"]')).toHaveCount(0);
  
  // Now drag card-1 to Discovery
  const card1 = page.getByTestId("card-card-1");
  await card1.dragTo(discoveryCol);
  
  // Verify card-1 is in Discovery
  await expect(discoveryCol.getByTestId("card-card-1")).toBeVisible();
});
