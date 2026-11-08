"use client";

import { useEffect, useState } from "react";

/** Bezel Charts uses browser-only features, so it loads in the browser, not on the server. */
export function useBezelCharts() {
  useEffect(() => {
    import("bezel-charts").catch(() => undefined);
  }, []);
}

/**
 * The card colour behind a chart. Bezel Charts draws some details in the tile's colour, so it has
 * to match the card in light and dark.
 */
export function useSurfaceColour() {
  const [colour, setColour] = useState<string | undefined>(undefined);
  useEffect(() => {
    const update = () =>
      setColour(getComputedStyle(document.documentElement).getPropertyValue("--surface").trim());
    update();
    const scheme = window.matchMedia?.("(prefers-color-scheme: dark)");
    scheme?.addEventListener("change", update);
    return () => scheme?.removeEventListener("change", update);
  }, []);
  return colour;
}
