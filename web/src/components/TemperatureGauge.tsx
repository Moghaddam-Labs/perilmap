"use client";

import { useBezelCharts, useSurfaceColour } from "@/lib/bezel";
import styles from "./TemperatureGauge.module.css";

interface TemperatureGaugeProps {
  value: number;
  low: number;
  high: number;
  unit: string;
  group: string;
}

/** A teal that reads on the card in both themes, and says nothing about good or bad. */
const GAUGE_COLOUR = "#3f9e8f";

/**
 * Where an area sits in London's temperature range, drawn by Bezel Charts. The card's summary says
 * the same thing in words, so the chart is an extra, never the only way to get the answer.
 */
export function TemperatureGauge({ value, low, high, unit, group }: TemperatureGaugeProps) {
  useBezelCharts();
  const background = useSurfaceColour();

  return (
    <div className={styles.gauge}>
      <bezel-gauge
        values={String(value)}
        min={String(low)}
        max={String(high)}
        suffix={` ${unit}`}
        decimals="1"
        labels={group.charAt(0).toUpperCase() + group.slice(1)}
        frame="none"
        color={GAUGE_COLOUR}
        background={background}
        height="150"
        lang="en-GB"
      />
    </div>
  );
}
