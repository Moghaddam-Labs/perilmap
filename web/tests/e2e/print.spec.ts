import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test, type Page } from "@playwright/test";

const API = "https://perilmap-api-762501502533.europe-west2.run.app";
const ASSESSMENT = JSON.parse(
  readFileSync(resolve(process.cwd(), "tests/e2e/fixtures/assessment-thames_wapping.json"), "utf8"),
);
const ZONE_MAP = JSON.parse(
  readFileSync(
    resolve(process.cwd(), "tests/e2e/fixtures/zone-map-thames_wapping-rivers_and_sea.json"),
    "utf8",
  ),
);
const BLANK_STYLE = {
  version: 8,
  sources: {},
  layers: [{ id: "background", type: "background", paint: { "background-color": "#e6ebe8" } }],
};

async function showResults(page: Page, { mapStyles = true } = {}) {
  if (mapStyles) {
    await page.route("https://tiles.openfreemap.org/styles/*", (route) =>
      route.fulfill({ json: BLANK_STYLE }),
    );
  }
  await page.route(`${API}/v1/postcodes/lookup`, (route) =>
    route.fulfill({
      json: { postcode: "E1W 1AA", latitude: 51.5045, longitude: -0.056, attribution: "x" },
    }),
  );
  await page.route(`${API}/v1/assessments`, (route) => route.fulfill({ json: ASSESSMENT }));
  await page.route(`${API}/v1/zone-maps`, (route) => route.fulfill({ json: ZONE_MAP }));
  await page.goto("/");
  await page.getByLabel("Postcode").fill("E1W 1AA");
  await page.getByRole("button", { name: "Find postcode" }).click();
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: "Check this location" }).click();
  await expect(page.getByRole("article").first()).toBeVisible();
  await expect(page.getByText(/Showing rivers and sea flood zones/)).toBeVisible();
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
  await expect(page.getByRole("group", { name: "Flood zones on the map" })).toBeHidden();
  await expect(page.getByText(/Showing rivers and sea flood zones/)).toBeVisible();
  await expect(page.getByRole("list", { name: "Map key" })).toBeVisible();
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

test("in dark mode, the print button prints the light map, then puts the dark map back", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "dark" });
  const styles: string[] = [];
  await page.route("https://tiles.openfreemap.org/styles/*", (route) => {
    const name = new URL(route.request().url()).pathname.split("/").pop() ?? "";
    styles.push(name);
    const colour = name === "dark" ? "#101010" : "#f0f0f0";
    return route.fulfill({
      json: {
        version: 8,
        sources: {},
        layers: [{ id: "bg", type: "background", paint: { "background-color": colour } }],
      },
    });
  });
  await showResults(page, { mapStyles: false });
  await page.evaluate(() => {
    window.print = () => {};
  });
  await page.getByRole("button", { name: "Print or save as PDF" }).click();
  await expect(page.locator("img[data-map-snapshot]")).toHaveAttribute("src", /^data:image\/png/);
  // Reads one pixel from the corner of the printed map image.
  const corner = await page.locator("img[data-map-snapshot]").evaluate(async (image) => {
    const img = image as HTMLImageElement;
    await img.decode();
    const canvas = document.createElement("canvas");
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const context = canvas.getContext("2d");
    context?.drawImage(img, 0, 0);
    return Array.from(context?.getImageData(2, 2, 1, 1).data ?? []);
  });
  expect(corner.slice(0, 3)).toEqual([240, 240, 240]);
  await expect.poll(() => styles.at(-1)).toBe("dark");
  expect(styles).toContain("positron");
});
