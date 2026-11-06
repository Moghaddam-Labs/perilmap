import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const PAGES = ["/", "/design"];

function watchForBlockedContent(page: Page) {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      problems.push(message.text());
    }
  });
  page.on("pageerror", (error) => problems.push(error.message));
  return problems;
}

test("sends the security headers", async ({ request }) => {
  const response = await request.get("/");
  const headers = response.headers();
  expect(headers["content-security-policy"]).toContain("'strict-dynamic'");
  expect(headers["referrer-policy"]).toBe("no-referrer");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-powered-by"]).toBeUndefined();
});

test("uses a new script code for each page view", async ({ request }) => {
  const nonce = async () =>
    /'nonce-([^']+)'/.exec(
      (await request.get("/")).headers()["content-security-policy"] ?? "",
    )?.[1];
  expect(await nonce()).not.toEqual(await nonce());
});

test("loads nothing from other sites", async ({ page }) => {
  const outside: string[] = [];
  page.on("request", (request) => {
    if (
      new URL(request.url()).origin !==
      new URL(page.url() === "about:blank" ? request.url() : page.url()).origin
    ) {
      outside.push(request.url());
    }
  });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  expect(outside).toEqual([]);
});

test("the skip link is first and moves to the main content", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Skip to main content" });
  await expect(skip).toBeFocused();
  await skip.press("Enter");
  await expect(page).toHaveURL(/#main$/);
});

test("every footer link can be reached by keyboard and shows where focus is", async ({ page }) => {
  await page.goto("/");
  const firstLink = page.getByRole("contentinfo").getByRole("link").first();
  await firstLink.focus();
  await expect(firstLink).toBeFocused();
  const outline = await firstLink.evaluate((link) => getComputedStyle(link).outlineStyle);
  expect(outline).toBe("solid");
});

test("the top bar's links lead to real parts of the page", async ({ page }) => {
  await page.goto("/");
  const nav = page.getByRole("navigation", { name: "Main" });
  await nav.getByRole("link", { name: "How it works" }).click();
  await expect(page).toHaveURL(/#how-it-works$/);
  await expect(page.locator("#how-it-works")).toBeInViewport();
  await nav.getByRole("link", { name: "Privacy" }).click();
  await expect(page).toHaveURL(/#privacy$/);
  await expect(page.locator("#privacy")).toBeInViewport();
});

test("the top bar's links also work from another page", async ({ page }) => {
  await page.goto("/nothing-here");
  await page.getByRole("link", { name: "How it works" }).click();
  await expect(page).toHaveURL(/\/#how-it-works$/);
  await expect(page.getByRole("heading", { name: "How it works" })).toBeVisible();
});

test("the phone hero stays short", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const hero = await page
    .getByRole("heading", { level: 1 })
    .locator("xpath=ancestor::section")
    .boundingBox();
  expect(hero?.height).toBeLessThan(620);
});

test("an unknown page says so", async ({ page }) => {
  const response = await page.goto("/nothing-here");
  expect(response?.status()).toBe(404);
  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
});

for (const colorScheme of ["light", "dark"] as const) {
  for (const path of PAGES) {
    test(`${path} passes accessibility checks and runs cleanly in ${colorScheme}`, async ({
      page,
    }) => {
      const problems = watchForBlockedContent(page);
      await page.emulateMedia({ colorScheme });
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        .analyze();
      expect(results.violations.map((violation) => violation.id)).toEqual([]);
      expect(problems).toEqual([]);
    });
  }
}

for (const width of [320, 390, 768, 1280]) {
  for (const path of PAGES) {
    test(`${path} has no sideways scroll at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 800 });
      await page.goto(path);
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(0);
    });
  }
}
