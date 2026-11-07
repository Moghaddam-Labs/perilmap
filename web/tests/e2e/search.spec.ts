import { expect, test, type Page } from "@playwright/test";

// Tests never reach the real API or map service. These stand in for them.
const API = "https://perilmap-api-762501502533.europe-west2.run.app";
const BLANK_STYLE = {
  version: 8,
  sources: {},
  layers: [{ id: "background", type: "background", paint: { "background-color": "#e6ebe8" } }],
};

async function standIns(page: Page, postcode: { status: number; body: unknown }) {
  const lookups: { url: string; method: string; body: string | null }[] = [];
  await page.route("https://tiles.openfreemap.org/styles/*", (route) =>
    route.fulfill({ json: BLANK_STYLE }),
  );
  await page.route(`${API}/**`, (route) => {
    const request = route.request();
    lookups.push({ url: request.url(), method: request.method(), body: request.postData() });
    return route.fulfill({ status: postcode.status, json: postcode.body });
  });
  return lookups;
}

const WESTMINSTER = {
  status: 200,
  body: {
    postcode: "SW1A 2AA",
    latitude: 51.5035,
    longitude: -0.1276,
    attribution: "Postcode lookup by postcodes.io",
  },
};

async function findPostcode(page: Page, text: string) {
  await page.goto("/");
  await page.getByLabel("Postcode").fill(text);
  await page.getByRole("button", { name: "Find postcode" }).click();
}

test("finding a postcode opens the map with the pin at its centre", async ({ page }) => {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") problems.push(message.text());
  });
  page.on("pageerror", (error) => problems.push(error.message));
  const lookups = await standIns(page, WESTMINSTER);
  await findPostcode(page, "sw1a2aa");

  const heading = page.getByRole("heading", { level: 2, name: "Mark the home on the map" });
  await expect(heading).toBeFocused();
  await expect(page.getByText("The pin is at the postcode's centre.")).toBeVisible();
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();

  expect(lookups).toEqual([
    {
      url: `${API}/v1/postcodes/lookup`,
      method: "POST",
      body: JSON.stringify({ postcode: "SW1A 2AA" }),
    },
  ]);
  await expect(page).toHaveURL(/\/$/);
  expect(problems).toEqual([]);
});

test("the pin can be moved with the keyboard, and says where it is", async ({ page }) => {
  await standIns(page, WESTMINSTER);
  await findPostcode(page, "SW1A 2AA");
  const pin = page.getByRole("button", { name: /Pin marking the home/ });
  await pin.focus();
  await pin.press("Shift+ArrowRight");
  await pin.press("Shift+ArrowRight");
  await expect(
    page.getByText(/The pin is about \d+ m east of the postcode's centre\./),
  ).toBeVisible();

  await page.getByRole("button", { name: "Move the pin back to the centre" }).click();
  await expect(page.getByText("The pin is at the postcode's centre.")).toBeVisible();
});

test("clicking the map moves the pin there", async ({ page }) => {
  await standIns(page, WESTMINSTER);
  await findPostcode(page, "SW1A 2AA");
  const canvas = page.locator(".maplibregl-canvas");
  await expect(canvas).toBeVisible();
  const box = await canvas.boundingBox();
  if (!box) throw new Error("The map has no size");
  await page.mouse.click(box.x + box.width / 2, box.y + 40);
  await expect(
    page.getByText(/The pin is about \d+ m north of the postcode's centre\./),
  ).toBeVisible();
});

test("a postcode outside London is explained, and no map opens", async ({ page }) => {
  await standIns(page, {
    status: 200,
    body: { ...WESTMINSTER.body, postcode: "RG1 1AA", latitude: 51.4543, longitude: -0.9781 },
  });
  await findPostcode(page, "RG1 1AA");
  await expect(page.getByText(/RG1 1AA is outside Greater London/)).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 2, name: "Mark the home on the map" }),
  ).toHaveCount(0);
});

test("an error on a phone doesn't shift the header sideways", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 700 });
  await page.goto("/");
  await page.getByRole("button", { name: "Find postcode" }).click();
  await expect(page.getByText("Enter a postcode.")).toBeVisible();
  const shift = await page
    .getByRole("heading", { level: 1 })
    .evaluate((heading) => heading.closest("section")?.scrollLeft ?? 0);
  expect(shift).toBe(0);
  const form = await page.locator("form").boundingBox();
  const box = await page.getByRole("button", { name: "Find postcode" }).boundingBox();
  expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(
    (form?.x ?? 0) + (form?.width ?? 0),
  );
});

test("a busy API gets a clear message", async ({ page }) => {
  await standIns(page, { status: 429, body: { detail: "Too many requests" } });
  await findPostcode(page, "SW1A 2AA");
  await expect(page.getByText(/too many searches in a short time/)).toBeVisible();
  await expect(page.getByLabel("Postcode")).toBeFocused();
});

test("if the map can't load, the location can still be checked", async ({ page }) => {
  await standIns(page, WESTMINSTER);
  await page.route("https://tiles.openfreemap.org/styles/*", (route) => route.abort());
  await findPostcode(page, "SW1A 2AA");
  await expect(page.getByText("The map couldn't load")).toBeVisible();
  await expect(page.getByRole("button", { name: "Check this location" })).toBeEnabled();
});

test("the map section passes accessibility checks", async ({ page }) => {
  const { default: AxeBuilder } = await import("@axe-core/playwright");
  await standIns(page, WESTMINSTER);
  await findPostcode(page, "SW1A 2AA");
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(
    results.violations.map((violation) => `${violation.id}: ${violation.nodes[0]?.target}`),
  ).toEqual([]);
});

test("the map's worker is served by the site, as JavaScript", async ({ request }) => {
  const response = await request.get("/vendor/maplibre-gl-worker.mjs");
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toMatch(/javascript/);
});
