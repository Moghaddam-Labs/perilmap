import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ResultCard } from "@/components/ResultCard";
import { assessLocation } from "@/lib/api/client";
import type { Assessment, PerilResult } from "@/lib/api/types";

const fixture = (name: string) =>
  JSON.parse(
    readFileSync(resolve(process.cwd(), `tests/e2e/fixtures/assessment-${name}.json`), "utf8"),
  ) as Assessment;

const result = (name: string, perilId: string) =>
  fixture(name).results.find((item) => item.peril_id === perilId) as PerilResult;

afterEach(() => vi.unstubAllGlobals());

describe("ResultCard", () => {
  it("shows the three answers every result gives", () => {
    render(<ResultCard result={result("thames_wapping", "flood_surface_water")} />);
    for (const heading of ["What this means", "How sure this is", "What you can do"]) {
      expect(screen.getByRole("heading", { name: heading })).toBeTruthy();
    }
  });

  it("lists each flood level's nearest zone in a table", () => {
    render(<ResultCard result={result("thames_wapping", "flood_rivers_and_sea")} />);
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows.map((row) => row.textContent)).toEqual([
      "HighAbout 40 m",
      "MediumAbout 40 m",
      "LowAbout 30 m",
      "Very LowOn the zone, or within about 5 m",
    ]);
  });

  it("labels a result with no data", () => {
    render(<ResultCard result={result("river_edge", "heat")} />);
    expect(screen.getByText("No data")).toBeTruthy();
  });

  it("marks London-wide information as general, not a result for the home", () => {
    render(<ResultCard result={result("thames_wapping", "subsidence")} />);
    expect(screen.getByText("General information")).toBeTruthy();
  });

  it("says which figures are PerilMap's own calculation", () => {
    render(<ResultCard result={result("thames_wapping", "heat")} />);
    expect(screen.getByText(/PerilMap's own calculation/)).toBeTruthy();
  });

  it("credits the source", () => {
    render(<ResultCard result={result("thames_wapping", "flood_rivers_and_sea")} />);
    expect(screen.getByText(/© Environment Agency copyright/)).toBeTruthy();
  });

  it("won't link to an unsafe address, even from the API", () => {
    const unsafe = {
      ...result("thames_wapping", "heat"),
      links: [{ label: "Guidance", url: "javascript:alert(1)" }],
    };
    render(<ResultCard result={unsafe} />);
    expect(screen.queryByRole("link", { name: /Guidance/ })).toBeNull();
  });
});

describe("assessLocation", () => {
  it("sends the location in the body, rounded to about 10 cm", async () => {
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify(fixture("ealing")), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await assessLocation({ latitude: 51.50031234567, longitude: -0.30651234567 });
    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/v1\/assessments$/);
    expect(options.body).toBe(JSON.stringify({ latitude: 51.500312, longitude: -0.306512 }));
  });

  it("refuses an answer that isn't shaped like an assessment", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 200 })),
    );
    await expect(assessLocation({ latitude: 51.5, longitude: -0.1 })).rejects.toMatchObject({
      problem: "unavailable",
    });
  });
});
