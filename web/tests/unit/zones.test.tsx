import { fireEvent, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Notice } from "@/components/Notice";
import { ZoneMapControls, type ZoneMapState } from "@/components/ZoneMapControls";
import { fetchZoneMap } from "@/lib/api/client";
import type { ZoneMap } from "@/lib/api/types";
import { LIVE_API_URL } from "@/lib/config";
import { distanceMetres } from "@/lib/geo";
import {
  FLOOD_MAP_LAYERS,
  NO_DATA,
  circleBounds,
  searchCircle,
  shownBands,
  zoneFeatures,
} from "@/lib/zoneMap";

const RING: [number, number][] = [
  [-0.3, 51.5],
  [-0.299, 51.5],
  [-0.299, 51.501],
  [-0.3, 51.5],
];

const ZONE_MAP: ZoneMap = {
  peril_id: "flood_rivers_and_sea",
  search_radius_metres: 1000,
  shapes: [
    { band: "High", coordinates: [[RING]] },
    { band: "Medium", coordinates: [[RING]] },
    { band: "Very Low", coordinates: [[RING]] },
  ],
  no_data_areas: [],
};

const SPOT = { latitude: 51.5085, longitude: -0.3016 };

afterEach(() => vi.unstubAllGlobals());

describe("fetchZoneMap", () => {
  it("sends the spot and check in the body, rounded, never in the web address", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(ZONE_MAP)));
    vi.stubGlobal("fetch", fetchMock);
    const spot = { latitude: 51.50851234, longitude: -0.30161234 };
    await expect(fetchZoneMap(spot, "flood_rivers_and_sea")).resolves.toEqual(ZONE_MAP);
    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${LIVE_API_URL}/v1/zone-maps`);
    expect(url).not.toContain("51.5");
    expect(JSON.parse(options.body as string)).toEqual({
      latitude: 51.508512,
      longitude: -0.301612,
      peril_id: "flood_rivers_and_sea",
    });
  });

  it.each([
    ["a shape missing its band", { ...ZONE_MAP, shapes: [{ coordinates: [] }] }],
    ["another check's map", { ...ZONE_MAP, peril_id: "flood_surface_water" }],
    ["no shapes list", { ...ZONE_MAP, shapes: null }],
  ])("refuses %s", async (_, body) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(body))),
    );
    await expect(fetchZoneMap(SPOT, "flood_rivers_and_sea")).rejects.toMatchObject({
      problem: "unavailable",
    });
  });
});

describe("zone features", () => {
  it("draws the lowest band first so higher bands sit on top", () => {
    const bands = zoneFeatures(ZONE_MAP).features.map((feature) => feature.properties.band);
    expect(bands).toEqual(["Very Low", "Medium", "High"]);
  });

  it("marks areas with no data on top, with the neutral pattern", () => {
    const features = zoneFeatures({ ...ZONE_MAP, no_data_areas: [[RING]] }).features;
    expect(features.at(-1)?.properties).toEqual({ band: NO_DATA, pattern: "other" });
  });

  it("draws nothing before the zones arrive", () => {
    expect(zoneFeatures(null).features).toEqual([]);
  });

  it("lists the key highest band first", () => {
    expect(shownBands(ZONE_MAP)).toEqual({ bands: ["High", "Medium", "Very Low"], noData: false });
  });

  it("draws the search circle at the right distance all the way round", () => {
    const circle = searchCircle(SPOT, 1000);
    const ring = circle.geometry.coordinates[0] ?? [];
    expect(ring[0]).toEqual(ring.at(-1));
    for (const [longitude, latitude] of ring) {
      const metres = distanceMetres(SPOT, { latitude: latitude!, longitude: longitude! });
      expect(metres).toBeCloseTo(1000, -1);
    }
    const [[west, south], [east, north]] = circleBounds(circle);
    expect(west).toBeLessThan(SPOT.longitude);
    expect(east).toBeGreaterThan(SPOT.longitude);
    expect(south).toBeLessThan(SPOT.latitude);
    expect(north).toBeGreaterThan(SPOT.latitude);
  });

  it("offers rivers and sea first, then surface water", () => {
    expect(FLOOD_MAP_LAYERS.map((layer) => layer.label)).toEqual([
      "Rivers and sea",
      "Surface water",
    ]);
  });
});

function controls(state: ZoneMapState | null, overrides = {}) {
  const onChoose = vi.fn();
  const onRetry = vi.fn();
  const view = render(
    <ZoneMapControls
      layers={FLOOD_MAP_LAYERS}
      chosen="flood_rivers_and_sea"
      state={state}
      radiusMetres={1000}
      stale={false}
      onChoose={onChoose}
      onRetry={onRetry}
      {...overrides}
    />,
  );
  return { ...view, onChoose, onRetry };
}

describe("ZoneMapControls", () => {
  it("is a labelled group of choices with no accessibility problems", async () => {
    const { container } = controls({ status: "ready", zoneMap: ZONE_MAP });
    expect(screen.getByRole("group", { name: "Flood zones on the map" })).toBeTruthy();
    expect(screen.getByRole("radio", { name: "Rivers and sea" })).toHaveProperty("checked", true);
    const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(results.violations.map((violation) => violation.id)).toEqual([]);
  });

  it("says what's drawn and lists only the levels on the map", () => {
    controls({ status: "ready", zoneMap: ZONE_MAP });
    expect(
      screen.getByText("Showing rivers and sea flood zones within 1 km of the checked spot."),
    ).toBeTruthy();
    const key = screen.getByRole("list", { name: "Map key" });
    const rows = [...key.querySelectorAll("strong")].map((row) => row.textContent);
    expect(rows).toEqual(["High", "Medium", "Very Low", "Search area"]);
  });

  it("says when there are no zones nearby, without calling the area safe", () => {
    controls({ status: "ready", zoneMap: { ...ZONE_MAP, shapes: [] } });
    const status = screen.getByText(/no mapped rivers and sea flood zones within 1 km/);
    expect(status.textContent).not.toMatch(/safe|no risk/i);
  });

  it("keys areas with no data, so they can't be read as clear", () => {
    controls({ status: "ready", zoneMap: { ...ZONE_MAP, no_data_areas: [[RING]] } });
    expect(screen.getByText("No data")).toBeTruthy();
    expect(screen.getByText(/can't be called clear/)).toBeTruthy();
  });

  it("announces loading, and offers to try again after a failure", () => {
    const loading = controls({ status: "loading" });
    expect(screen.getByText("Loading rivers and sea flood zones")).toBeTruthy();
    loading.unmount();
    const { onRetry } = controls({ status: "failed", message: "The flood zones couldn't load." });
    expect(screen.getByRole("alert").textContent).toContain("The results below aren't affected.");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalled();
  });

  it("reports a new choice, including none", () => {
    const { onChoose } = controls({ status: "ready", zoneMap: ZONE_MAP });
    fireEvent.click(screen.getByRole("radio", { name: "Surface water" }));
    fireEvent.click(screen.getByRole("radio", { name: "None" }));
    expect(onChoose.mock.calls).toEqual([["flood_surface_water"], ["none"]]);
  });

  it("says when the pin has moved since the map was drawn", () => {
    controls({ status: "ready", zoneMap: ZONE_MAP }, { stale: true });
    expect(screen.getByText(/check again to update the map/)).toBeTruthy();
  });
});

describe("Notice", () => {
  it("keeps the class it's given, so it can be left off printouts", () => {
    const { container } = render(
      <Notice title="Hello" className="no-print">
        Body
      </Notice>,
    );
    expect(container.firstElementChild?.classList.contains("no-print")).toBe(true);
  });
});
