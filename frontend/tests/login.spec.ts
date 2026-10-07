import { expect, test } from "@playwright/test";

test.describe("Login flow", () => {
  test("redirects to login when unauthenticated", async ({ page }) => {
    await page.goto("/");
    // Should be redirected to /login
    await page.waitForURL("**/login");
    await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
    await expect(page.getByPlaceholder("user")).toBeVisible();
  });

  test("shows error on invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[placeholder="user"]', "wrong");
    await page.fill('input[placeholder="password"]', "wrong");
    await page.click('button:has-text("Sign In")');

    await expect(page.getByText("Invalid credentials")).toBeVisible();
  });

  test("logs in and logs out successfully", async ({ page }) => {
    // 1. Login
    await page.goto("/login");
    await page.fill('input[placeholder="user"]', "user");
    await page.fill('input[placeholder="password"]', "password");
    await page.click('button:has-text("Sign In")');

    // 2. See board
    await page.waitForURL("**/");
    await expect(page.getByText("Single Board Kanban")).toBeVisible();

    // 3. Logout
    await page.click('button:has-text("Logout")');

    // 4. Return to login
    await page.waitForURL("**/login");
    await expect(page.getByPlaceholder("user")).toBeVisible();
    
    // 5. Try accessing the root again directly
    await page.goto("/");
    await page.waitForURL("**/login");
  });
});

