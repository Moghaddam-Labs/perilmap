import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test, type Page } from "@playwright/test";

const API = "https://perilmap-api-762501502533.europe-west2.run.app";
const ASSESSMENT = JSON.parse(
  readFileSync(resolve(process.cwd(), "tests/e2e/fixtures/assessment-thames_wapping.json"), "utf8"),
);
const BLANK_STYLE = {
  version: 8,
  sources: {},
  layers: [{ id: "background", type: "background", paint: { "background-color": "#e6ebe8" } }],
};

async function showResults(page: Page) {
  await page.route("https://tiles.openfreemap.org/styles/*", (route) =>
    route.fulfill({ json: BLANK_STYLE }),
  );
  await page.route(`${API}/v1/postcodes/lookup`, (route) =>
    route.fulfill({
      json: { postcode: "E1W 1AA", latitude: 51.5045, longitude: -0.056, attribution: "x" },
    }),
  );
  await page.route(`${API}/v1/assessments`, (route) => route.fulfill({ json: ASSESSMENT }));
  await page.goto("/");
  await page.getByLabel("Postcode").fill("E1W 1AA");
  await page.getByRole("button", { name: "Find postcode" }).click();
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: "Check this location" }).click();
  await expect(page.getByRole("article").first()).toBeVisible();
}

test("printing gets the whole report ready, then puts the page back", async ({ page }) => {
  await showResults(page);
  await page.evaluate(() => {
    const record = window as unknown as { printed: unknown[] };
    record.printed = [];
    window.print = () => {
      record.printed.push({
        title: document.title,
        theme: document.documentElement.getAttribute("data-theme"),
        allOpen: [...document.querySelectorAll("article details")].every(
          (details) => (details as HTMLDetailsElement).open,
        ),
        map: document.querySelector<HTMLImageElement>("img[data-map-snapshot]")?.src.slice(0, 22),
      });
    };
  });
  await page.getByRole("button", { name: "Print or save as PDF" }).click();
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { printed: unknown[] }).printed))
    .toEqual([
      {
        title: "PerilMap report near E1W 1AA",
        theme: "light",
        allOpen: true,
        map: "data:image/png;base64,",
      },
    ]);
  await expect(page).toHaveTitle("PerilMap: climate risks around a home");
  const stillOpen = await page
    .locator("article details")
    .evaluateAll((all) => all.some((details) => (details as HTMLDetailsElement).open));
  expect(stillOpen).toBe(false);
  expect(await page.evaluate(() => document.documentElement.hasAttribute("data-theme"))).toBe(
    false,
  );
});

test("on paper, only the report, the map image and the credits show", async ({ page }) => {
  await showResults(page);
  await page.emulateMedia({ media: "print" });
  await expect(page.getByText("PerilMap report")).toBeVisible();
  await expect(
    page.getByText(/Near E1W 1AA\. The pin is at the postcode's centre\./),
  ).toBeVisible();
  await expect(page.getByLabel("Postcode")).toBeHidden();
  await expect(page.locator(".maplibregl-canvas")).toBeHidden();
  await expect(page.getByRole("button", { name: "Check this location" })).toBeHidden();
  await expect(page.getByRole("button", { name: "Print or save as PDF" })).toBeHidden();
  await expect(page.getByRole("heading", { name: "What PerilMap looks at" })).toBeHidden();
  await expect(page.getByText(/© Environment Agency copyright/).last()).toBeVisible();
  await expect(page.getByRole("article")).toHaveCount(4);
});

test("out of date results can't be printed", async ({ page }) => {
  await showResults(page);
  const pin = page.getByRole("button", { name: /Pin marking the home/ });
  await pin.focus();
  await pin.press("ArrowLeft");
  await expect(page.getByText("You've moved the pin")).toBeVisible();
  await expect(page.getByRole("button", { name: "Print or save as PDF" })).toHaveCount(0);
});

test("dark mode still prints in light colours", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await showResults(page);
  await page.evaluate(() => {
    window.print = () => {
      (window as unknown as { paper: string }).paper = getComputedStyle(
        document.documentElement,
      ).getPropertyValue("--surface");
    };
  });
  await page.getByRole("button", { name: "Print or save as PDF" }).click();
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { paper?: string }).paper?.trim()))
    .toMatch(/^#fff(fff)?$/);
});
