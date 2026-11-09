import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen, within } from "@testing-library/react";
import axe from "axe-core";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import AboutPage from "@/app/about/page";
import FloodInsurancePage from "@/app/flood-insurance/page";
import PrivacyPage from "@/app/privacy/page";
import { ResultsSection } from "@/components/ResultsSection";
import { DISCLAIMER } from "@/components/SiteFooter";
import type { Assessment } from "@/lib/api/types";
import { DATA_SOURCES } from "@/lib/dataSources";
import { NOT_COVERED } from "@/lib/notCovered";

const fixture = (name: string) =>
  JSON.parse(
    readFileSync(resolve(process.cwd(), `tests/e2e/fixtures/assessment-${name}.json`), "utf8"),
  ) as Assessment;

async function violations(ui: ReactElement) {
  const { container } = render(ui);
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((violation) => violation.id);
}

describe.each([
  ["Privacy", PrivacyPage],
  ["About the data", AboutPage],
  ["Flood insurance and Flood Re", FloodInsurancePage],
])("the %s page", (title, Page) => {
  it("has one main heading, a date, and no accessibility problems", async () => {
    expect(await violations(<Page />)).toEqual([]);
    expect(screen.getAllByRole("heading", { level: 1 }).map((h) => h.textContent)).toEqual([title]);
    expect(screen.getByText(/^Last updated \d{1,2} \w+ \d{4}$/)).toBeTruthy();
  });

  it("avoids em dashes and never calls an area safe", () => {
    const { container } = render(<Page />);
    const text = container.textContent ?? "";
    expect(text).not.toContain("—");
    expect(text).not.toMatch(/\bis safe\b|\bno risk\b|\brisk-free\b/i);
  });

  it("opens every outside link safely in a new tab, and says so", () => {
    const { container } = render(<Page />);
    for (const link of container.querySelectorAll<HTMLAnchorElement>("a[href^='http']")) {
      expect(link.href).toMatch(/^https:\/\//);
      expect(link.target).toBe("_blank");
      expect(link.rel).toContain("noopener");
      expect(link.textContent).toContain("opens in a new tab");
    }
  });
});

describe("the privacy page", () => {
  it("names every service that sees a request, with its own policy", () => {
    render(<PrivacyPage />);
    for (const name of ["Vercel", "Google Cloud", "postcodes.io", "OpenFreeMap"]) {
      expect(screen.getByRole("heading", { level: 3, name: new RegExp(`^${name}`) })).toBeTruthy();
    }
    expect(screen.getByText(/doesn't use cookies, analytics, adverts or tracking/)).toBeTruthy();
  });
});

describe("the About the data page", () => {
  it("leads with the same disclaimer as the results", () => {
    render(<AboutPage />);
    expect(screen.getByText(DISCLAIMER)).toBeTruthy();
  });

  it("lists every data source with its date", () => {
    render(<AboutPage />);
    const section = screen.getByRole("region", { name: "Where the data comes from" });
    for (const source of DATA_SOURCES) {
      expect(within(section).getAllByText(source.updated).length).toBeGreaterThan(0);
    }
  });

  it("lists exactly what the API says isn't covered", () => {
    expect(NOT_COVERED).toEqual(fixture("thames_wapping").not_covered);
    render(<AboutPage />);
    const section = screen.getByRole("region", { name: "What PerilMap doesn't cover" });
    expect(
      within(section)
        .getAllByRole("listitem")
        .map((item) => item.textContent),
    ).toEqual(NOT_COVERED);
  });

  it("explains each gap label the result cards use", () => {
    render(<AboutPage />);
    const section = screen.getByRole("region", { name: "When data is missing" });
    for (const label of ["No data", "May be incomplete", "Not available here yet"]) {
      expect(within(section).getByText(label)).toBeTruthy();
    }
  });
});

describe("the flood insurance page", () => {
  it("states Flood Re's 2009 cut off and that it isn't advice", () => {
    render(<FloodInsurancePage />);
    expect(screen.getByText("was built before 1 January 2009")).toBeTruthy();
    expect(screen.getByText(/not insurance advice/)).toBeTruthy();
  });
});

describe("Find out more under the results", () => {
  it("offers the flood insurance page when a flood zone is nearby", () => {
    render(
      <ResultsSection assessment={fixture("thames_wapping")} postcode="E1W 1AA" stale={false} />,
    );
    const more = screen.getByRole("heading", { name: "Find out more" }).parentElement!;
    expect(within(more).getByRole("link", { name: "About the data" }).getAttribute("href")).toBe(
      "/about",
    );
    expect(
      within(more).getByRole("link", { name: "Flood insurance and Flood Re" }).getAttribute("href"),
    ).toBe("/flood-insurance");
  });

  it("leaves the flood insurance page out when no flood zone is nearby", () => {
    const assessment = fixture("ealing");
    const clear: Assessment = {
      ...assessment,
      results: assessment.results.map((result) =>
        result.measurement?.type === "nearest_zones"
          ? {
              ...result,
              measurement: {
                ...result.measurement,
                zones: result.measurement.zones.map((zone) => ({ ...zone, metres: null })),
              },
            }
          : result,
      ),
    };
    render(<ResultsSection assessment={clear} postcode="W5 4HT" stale={false} />);
    expect(screen.getByRole("link", { name: "About the data" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "Flood insurance and Flood Re" })).toBeNull();
  });
});
