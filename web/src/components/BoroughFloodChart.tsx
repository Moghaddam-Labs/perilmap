"use client";

import { useBezelCharts, useSurfaceColour } from "@/lib/bezel";
import styles from "./BoroughFloodChart.module.css";

export interface BoroughShare {
  name: string;
  low_or_higher_percent: number;
  very_low_percent: number;
}

/**
 * Blue for Low or higher, from the flood level family, and a muted green-grey for Very Low. Both
 * read on the card in light and dark. Bezel Charts splits series names on commas, so neither name
 * may contain one.
 */
const COLOURS = "#3a8bd0,#7f938c";
const SERIES = "Low or higher,Very Low";

/**
 * Every borough's share of land in rivers and sea flood zones, stacked by level and drawn by Bezel
 * Charts. Wide screens get vertical bars with slanted names, phones get horizontal bars.
 */
export function BoroughFloodChart({ boroughs }: { boroughs: BoroughShare[] }) {
  useBezelCharts();
  const background = useSurfaceColour();
  const shared = {
    values: [
      boroughs.map((borough) => borough.low_or_higher_percent).join(","),
      boroughs.map((borough) => borough.very_low_percent).join(","),
    ].join("|"),
    labels: boroughs.map((borough) => borough.name.replaceAll(",", "")).join(","),
    series: SERIES,
    suffix: "%",
    decimals: "1",
    frame: "none" as const,
    color: COLOURS,
    background,
    lang: "en-GB",
  };
  return (
    <>
      <div className={styles.wide}>
        <bezel-bars {...shared} stacked angle-labels height="380" />
      </div>
      <div className={styles.narrow}>
        <bezel-bars {...shared} stacked horizontal />
        <p className={styles.note}>
          The number at the end of each bar is the total in any rivers and sea zone.
        </p>
      </div>
    </>
  );
}
