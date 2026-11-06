/** Map settings. The map images come from OpenFreeMap, which is free and needs no account or key. */

export const MAP_TILE_ORIGIN = "https://tiles.openfreemap.org";

export const MAP_STYLES = {
  light: `${MAP_TILE_ORIGIN}/styles/positron`,
  dark: `${MAP_TILE_ORIGIN}/styles/dark`,
} as const;

/** Served from the site by scripts/copy-map-worker.mjs. */
export const MAP_WORKER_PATH = "/vendor/maplibre-gl-worker.mjs";

/** How far the map can be moved: Greater London with some room around it. */
export const MAP_BOUNDS: [[number, number], [number, number]] = [
  [-0.85, 51.15],
  [0.65, 51.85],
];

/** Close enough to see individual buildings, so the pin can go on the right one. */
export const STREET_ZOOM = 17;
