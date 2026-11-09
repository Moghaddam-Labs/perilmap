/**
 * The flood level patterns as small repeating images for the map, matching the key's swatches.
 * Colours are read from the design tokens, so the map and the key can't drift apart.
 */

import type { BandPattern } from "@/lib/bands";

export const PATTERN_TILE = 28;
const PIXEL_RATIO = 2;

const TOKENS: Record<BandPattern, [fill: string, mark: string]> = {
  high: ["--band-high-fill", "--band-high-mark"],
  medium: ["--band-medium-fill", "--band-medium-mark"],
  low: ["--band-low-fill", "--band-low-mark"],
  veryLow: ["--band-very-low-fill", "--band-very-low-mark"],
  other: ["--band-other-fill", "--band-other-mark"],
};

export const PATTERNS = Object.keys(TOKENS) as BandPattern[];

export function patternImageId(pattern: BandPattern) {
  return `perilmap-pattern-${pattern}`;
}

export function tokenColour(name: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** Diagonals every 7 units, so the tile repeats without a seam. */
function diagonals(context: CanvasRenderingContext2D, reverse: boolean) {
  for (let offset = -PATTERN_TILE; offset <= PATTERN_TILE; offset += 7) {
    context.beginPath();
    if (reverse) {
      context.moveTo(PATTERN_TILE - offset, 0);
      context.lineTo(-offset, PATTERN_TILE);
    } else {
      context.moveTo(offset, 0);
      context.lineTo(PATTERN_TILE + offset, PATTERN_TILE);
    }
    context.stroke();
  }
}

function dots(context: CanvasRenderingContext2D, positions: number[], radius: number) {
  for (const x of positions) {
    for (const y of positions) {
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fill();
    }
  }
}

function drawMarks(context: CanvasRenderingContext2D, pattern: BandPattern) {
  switch (pattern) {
    case "high":
      diagonals(context, false);
      diagonals(context, true);
      break;
    case "medium":
      diagonals(context, false);
      break;
    case "low":
      dots(context, [3.5, 10.5, 17.5, 24.5], 1.9);
      break;
    case "veryLow":
      dots(context, [7, 21], 1.6);
      break;
    case "other":
      context.setLineDash([4, 3]);
      for (const y of [7, 21]) {
        context.beginPath();
        context.moveTo(0, y);
        context.lineTo(PATTERN_TILE, y);
        context.stroke();
      }
      break;
  }
}

/** One pattern tile, drawn at twice the size for sharp edges on high density screens. */
export function patternImage(
  pattern: BandPattern,
): { image: ImageData; pixelRatio: number } | null {
  const size = PATTERN_TILE * PIXEL_RATIO;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  if (!context) return null;
  const [fill, mark] = TOKENS[pattern].map(tokenColour) as [string, string];
  context.scale(PIXEL_RATIO, PIXEL_RATIO);
  context.fillStyle = fill;
  context.fillRect(0, 0, PATTERN_TILE, PATTERN_TILE);
  context.strokeStyle = mark;
  context.fillStyle = mark;
  context.lineWidth = 1.6;
  drawMarks(context, pattern);
  return { image: context.getImageData(0, 0, size, size), pixelRatio: PIXEL_RATIO };
}
