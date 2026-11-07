import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Real answers from the API, saved so the tests never depend on it.
const API = "https://perilmap-api-762501502533.europe-west2.run.app";
const fixture = (name: string) =>
  JSON.parse(
    readFileSync(resolve(process.cwd(), `tests/e2e/fixtures/assessment-${name}.json`), "utf8"),
  );
const BLANK_STYLE = {
  version: 8,
  sources: {},
  layers: [{ id: "background", type: "background", paint: { "background-color": "#e6ebe8" } }],
};
const POSTCODE = {
  postcode: "E1W 1AA",
  latitude: 51.5045,
  longitude: -0.056,
  attribution: "Postcode lookup by postcodes.io",
};

async function checkLocation(page: Page, answer: { status: number; body: unknown }) {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") problems.push(message.text());
  });
  page.on("pageerror", (error) => problems.push(error.message));
  const sent: unknown[] = [];
  await page.route("https://tiles.openfreemap.org/styles/*", (route) =>
    route.fulfill({ json: BLANK_STYLE }),
  );
  await page.route(`${API}/v1/postcodes/lookup`, (route) => route.fulfill({ json: POSTCODE }));
  await page.route(`${API}/v1/assessments`, (route) => {
    sent.push(route.request().postDataJSON());
    return route.fulfill({ status: answer.status, json: answer.body });
  });
  await page.goto("/");
  await page.getByLabel("Postcode").fill("E1W 1AA");
  await page.getByRole("button", { name: "Find postcode" }).click();
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await page.getByRole("button", { name: "Check this location" }).click();
  return { problems, sent };
}

test("checking a location shows a card for each peril", async ({ page }) => {
  const { problems, sent } = await checkLocation(page, {
    status: 200,
    body: fixture("thames_wapping"),
  });
  const heading = page.getByRole("heading", {
    level: 2,
    name: "What's around the pin near E1W 1AA",
  });
  await expect(heading).toBeFocused();
  for (const title of [
    "Flooding from rivers and sea",
    "Flooding from surface water",
    "Summer temperature",
    "Clay subsidence",
  ]) {
    await expect(page.getByRole("article", { name: title })).toBeVisible();
  }
  expect(sent).toEqual([{ latitude: 51.5045, longitude: -0.056 }]);
  expect(problems).toEqual([]);
});

test("flood cards list the nearest zone of each level, in words", async ({ page }) => {
  await checkLocation(page, { status: 200, body: fixture("thames_wapping") });
  const card = page.getByRole("article", { name: "Flooding from rivers and sea" });
  const rows = card.getByRole("row");
  await expect(rows).toHaveCount(5);
  await expect(card.getByRole("row", { name: /Very Low/ })).toContainText(
    "On the zone, or within about 5 m",
  );
});

test("the heat card draws Bezel Charts' gauge, with the same answer in words", async ({ page }) => {
  await checkLocation(page, { status: 200, body: fixture("thames_wapping") });
  const card = page.getByRole("article", { name: "Summer temperature" });
  await expect(card).toContainText("18.1 °C, among the warmer fifth");
  const gauge = card.locator("bezel-gauge");
  await expect(gauge).toBeVisible();
  const label = await gauge.evaluate(
    (element) => element.shadowRoot?.querySelector("svg")?.getAttribute("aria-label") ?? "",
  );
  expect(label).toContain("18.1");
  const box = await gauge.boundingBox();
  expect(box?.height).toBeGreaterThan(100);
});

test("a missing figure is labelled, not hidden", async ({ page }) => {
  await checkLocation(page, { status: 200, body: fixture("river_edge") });
  const card = page.getByRole("article", { name: "Summer temperature" });
  await expect(card.getByText("No data", { exact: true })).toBeVisible();
  await expect(card.locator("bezel-gauge")).toHaveCount(0);
});

test("no zones nearby is said plainly", async ({ page }) => {
  await checkLocation(page, { status: 200, body: fixture("ealing") });
  const card = page.getByRole("article", { name: "Flooding from rivers and sea" });
  await expect(card).toContainText("There's no mapped rivers and sea zone within 1,000 m");
  await expect(card.getByText("None within 1,000 m")).toHaveCount(4);
});

test("outside London, it explains why there are no results", async ({ page }) => {
  await checkLocation(page, { status: 200, body: fixture("reading") });
  await expect(
    page.getByRole("heading", { level: 2, name: "Not available here yet" }),
  ).toBeFocused();
  await expect(page.getByRole("article")).toHaveCount(0);
});

test("moving the pin after checking marks the results as out of date", async ({ page }) => {
  await checkLocation(page, { status: 200, body: fixture("thames_wapping") });
  await expect(page.getByRole("article").first()).toBeVisible();
  const pin = page.getByRole("button", { name: /Pin marking the home/ });
  await pin.focus();
  await pin.press("ArrowLeft");
  await expect(page.getByText("You've moved the pin")).toBeVisible();
  await page.getByRole("button", { name: "Check this location" }).click();
  await expect(page.getByText("You've moved the pin")).toHaveCount(0);
});

test("a failed check gets a clear message", async ({ page }) => {
  await checkLocation(page, { status: 503, body: { detail: "Down" } });
  await expect(page.getByRole("alert").filter({ hasText: "check this location" })).toContainText(
    "Results aren't available right now",
  );
});

for (const colorScheme of ["light", "dark"] as const) {
  test(`results pass accessibility checks in ${colorScheme}`, async ({ page }) => {
    await page.emulateMedia({ colorScheme });
    await checkLocation(page, { status: 200, body: fixture("thames_wapping") });
    await expect(page.locator("bezel-gauge")).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    expect(
      results.violations.map((violation) => `${violation.id}: ${violation.nodes[0]?.target}`),
    ).toEqual([]);
  });
}
