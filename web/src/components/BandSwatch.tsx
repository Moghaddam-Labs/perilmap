import type { BandPattern } from "@/lib/bands";
import styles from "./BandSwatch.module.css";

const GRID = [6, 14, 22];

function dots(positions: number[], radius: number) {
  return positions.flatMap((x) =>
    positions.map((y) => <circle key={`${x}-${y}`} cx={x} cy={y} r={radius} />),
  );
}

function diagonals(reverse = false) {
  return [-14, -7, 0, 7, 14].map((offset) => (
    <line
      key={offset}
      x1={reverse ? 28 - offset : offset}
      y1={0}
      x2={reverse ? -offset : 28 + offset}
      y2={28}
    />
  ));
}

const MARKS: Record<BandPattern, React.ReactNode> = {
  high: (
    <g className={styles.lines}>
      {diagonals()}
      {diagonals(true)}
    </g>
  ),
  medium: <g className={styles.lines}>{diagonals()}</g>,
  low: <g className={styles.dots}>{dots(GRID, 2)}</g>,
  veryLow: (
    <g className={styles.dots}>
      {dots([7, 21], 1.5)}
      <circle cx={14} cy={14} r={1.5} />
    </g>
  ),
  other: (
    <g className={styles.lines}>
      <line x1={3} y1={9} x2={25} y2={9} strokeDasharray="4 3" />
      <line x1={3} y1={19} x2={25} y2={19} strokeDasharray="4 3" />
    </g>
  ),
};

/** A map-legend square. Decorative, so always put the band's name in text beside it. */
export function BandSwatch({ pattern }: { pattern: BandPattern }) {
  return (
    <svg
      className={`${styles.swatch} ${styles[pattern]}`}
      viewBox="0 0 28 28"
      aria-hidden="true"
      focusable="false"
      data-pattern={pattern}
    >
      <rect width="28" height="28" className={styles.fill} />
      {MARKS[pattern]}
    </svg>
  );
}
