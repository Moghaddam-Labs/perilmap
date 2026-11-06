/**
 * Flood levels, using the Environment Agency's own names. Each has its own pattern as well as a
 * colour. A new plug-in's band still shows its own name, with a pattern that doesn't imply a level.
 */

export type BandPattern = "high" | "medium" | "low" | "veryLow" | "other";

export interface BandDisplay {
  label: string;
  pattern: BandPattern;
  chanceEachYear?: string;
}

const KNOWN_BANDS: Record<string, BandDisplay> = {
  High: { label: "High", pattern: "high", chanceEachYear: "1 in 30 or more" },
  Medium: {
    label: "Medium",
    pattern: "medium",
    chanceEachYear: "Between 1 in 30 and 1 in 100",
  },
  Low: { label: "Low", pattern: "low", chanceEachYear: "Between 1 in 100 and 1 in 1,000" },
  "Very Low": {
    label: "Very Low",
    pattern: "veryLow",
    chanceEachYear: "Below 1 in 1,000",
  },
};

export const FLOOD_BANDS = Object.values(KNOWN_BANDS);

export function bandDisplay(band: string): BandDisplay {
  return Object.hasOwn(KNOWN_BANDS, band)
    ? (KNOWN_BANDS[band] as BandDisplay)
    : { label: band, pattern: "other" };
}
