import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/styles/tokens.css"), "utf8");

function tokens(block: string) {
  return Object.fromEntries(
    [...block.matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})\s*;/gi)].map((m) => [m[1], m[2]]),
  ) as Record<string, string>;
}

const [lightCss, darkCss] = css.split("@media (prefers-color-scheme: dark)") as [string, string];
const light = tokens(lightCss);
const dark = { ...light, ...tokens(darkCss) };

function luminance(hex: string) {
  const channels = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const [r, g, b] = channels.map((c) =>
    c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4,
  ) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string) {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (high + 0.05) / (low + 0.05);
}

const TEXT = 4.5;
const INTERFACE = 3;

const PAIRS: [foreground: string, background: string, minimum: number][] = [
  ["ink", "paper", TEXT],
  ["ink", "surface", TEXT],
  ["ink-soft", "paper", TEXT],
  ["ink-soft", "surface", TEXT],
  ["link", "paper", TEXT],
  ["link", "surface", TEXT],
  ["error", "paper", TEXT],
  ["error", "surface", TEXT],
  ["paper", "ink", TEXT],
  ["paper", "ink-soft", TEXT],
  ["focus", "paper", INTERFACE],
  ["focus", "surface", INTERFACE],
  ["control-edge", "paper", INTERFACE],
  ["control-edge", "surface", INTERFACE],
  ["hero-ink", "brand-deep", TEXT],
  ["hero-ink-soft", "brand-deep", TEXT],
  ["hero-focus", "brand-deep", INTERFACE],
  ["hero-error", "brand-deep", TEXT],
  ["brand-deep", "brand-coral", TEXT],
  ["brand-coral", "brand-deep", INTERFACE],
  ["footer-ink", "footer-tone-a", TEXT],
  ["footer-ink", "footer-tone-b", TEXT],
  ["band-high-mark", "band-high-fill", INTERFACE],
  ["band-medium-mark", "band-medium-fill", INTERFACE],
  ["band-low-mark", "band-low-fill", INTERFACE],
  ["band-very-low-mark", "band-very-low-fill", INTERFACE],
  ["band-other-mark", "band-other-fill", INTERFACE],
];

describe.each([
  ["light", light],
  ["dark", dark],
])("%s theme colours", (_, theme) => {
  it.each(PAIRS)("%s on %s reaches %d:1", (foreground, background, minimum) => {
    const [a, b] = [theme[foreground], theme[background]];
    expect(a, `${foreground} is missing`).toBeDefined();
    expect(b, `${background} is missing`).toBeDefined();
    expect(contrast(a as string, b as string)).toBeGreaterThanOrEqual(minimum);
  });
});

it("gives each flood level a lighter fill than the one above it", () => {
  const fills = ["high", "medium", "low", "very-low"].map((name) =>
    luminance(light[`band-${name}-fill`] as string),
  );
  expect(fills).toEqual([...fills].sort((a, b) => a - b));
});
