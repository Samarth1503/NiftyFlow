import { test, expect } from "@playwright/test";

test("Securities page fetches bulk predictions and avoids N+1 requests", async ({ page }) => {
  let predictionRequests = 0;
  
  // Intercept all network requests
  page.on("request", (request) => {
    if (request.url().includes("/predictions")) {
      predictionRequests++;
    }
  });

  // Navigate to login page first to establish origin
  await page.goto("/login");
  
  // Set fake token in localStorage to bypass login
  await page.evaluate(() => {
    localStorage.setItem('token', 'fake-test-token');
  });

  // Intercept the API requests to return dummy data
  await page.route('**/api/v1/users/me', async route => {
    await route.fulfill({ json: { id: 1, email: "test@example.com", is_active: true } });
  });

  await page.route('**/api/v1/securities', async route => {
    await route.fulfill({ json: [
      { id: 1, symbol: "RELIANCE", name: "Reliance", exchange: "NSE" },
      { id: 2, symbol: "TCS", name: "TCS", exchange: "NSE" },
      { id: 3, symbol: "INFY", name: "Infosys", exchange: "NSE" }
    ] });
  });
  
  await page.route('**/api/v1/securities/predictions/bulk', async route => {
    await route.fulfill({ json: { 1: { predicted_score: 0.85, prediction_date: "2026-08-17" } } });
  });

  // Navigate directly to Market Data page
  await page.goto("/securities");
  
  // Wait for the securities to load
  await page.waitForSelector("h2:has-text('Market Data')");
  
  // Wait for the prediction mock text to appear
  await page.waitForSelector("text=85.00% Win Prob");

  // Verify that only 1 request was made for predictions
  // Even with multiple stocks loaded, we should not have N+1 requests
  // React 18 Strict Mode double-fetches, so 2 requests for the bulk endpoint is expected
  expect(predictionRequests).toBeLessThanOrEqual(2);
});
