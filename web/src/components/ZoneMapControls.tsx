"use client";

import { bandDisplay } from "@/lib/bands";
import type { MapLayerChoice } from "@/lib/zoneMap";
import type { ZoneMap } from "@/lib/api/types";
import { shownBands } from "@/lib/zoneMap";
import { BandSwatch } from "./BandSwatch";
import { Button } from "./Button";
import styles from "./ZoneMapControls.module.css";

export const NO_LAYER = "none";

export type ZoneMapState =
  | { status: "loading" }
  | { status: "ready"; zoneMap: ZoneMap }
  | { status: "failed"; message: string };

interface ZoneMapControlsProps {
  layers: readonly MapLayerChoice[];
  chosen: string;
  state: ZoneMapState | null;
  radiusMetres: number;
  stale: boolean;
  onChoose: (perilId: string) => void;
  onRetry: () => void;
}

function distance(metres: number) {
  return metres >= 1_000 ? `${metres / 1_000} km` : `${metres} m`;
}

/** Chooses which flood zones the map shows, says what's drawn, and gives the key. */
export function ZoneMapControls({
  layers,
  chosen,
  state,
  radiusMetres,
  stale,
  onChoose,
  onRetry,
}: ZoneMapControlsProps) {
  const layer = layers.find((choice) => choice.perilId === chosen);
  const zoneMap = state?.status === "ready" ? state.zoneMap : null;
  const { bands, noData } = shownBands(zoneMap);
  const area = distance(radiusMetres);
  const name = layer?.label.toLowerCase() ?? "";

  let status = `No flood zones are drawn. The circle shows the ${area} searched around the checked spot.`;
  if (layer && state?.status === "loading") status = `Loading ${name} flood zones`;
  if (layer && state?.status === "failed") status = "";
  if (layer && zoneMap) {
    status = bands.length
      ? `Showing ${name} flood zones within ${area} of the checked spot.`
      : `There are no mapped ${name} flood zones within ${area} of the checked spot.`;
  }

  return (
    <div className={styles.controls}>
      <fieldset className={`${styles.choice} no-print`}>
        <legend className={styles.legend}>Flood zones on the map</legend>
        <div className={styles.options}>
          {[...layers, { perilId: NO_LAYER, label: "None" }].map((option) => (
            <label key={option.perilId} className={styles.option}>
              <input
                type="radio"
                name="zone-map-layer"
                value={option.perilId}
                checked={chosen === option.perilId}
                onChange={() => onChoose(option.perilId)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <p className={styles.status} aria-live="polite">
        {status}
        {stale && " The pin has moved since then, so check again to update the map."}
      </p>

      {layer && state?.status === "failed" && (
        <div className={`${styles.failed} no-print`} role="alert">
          <p>{state.message} The results below aren&apos;t affected.</p>
          <Button variant="secondary" onClick={onRetry}>
            Try again
          </Button>
        </div>
      )}

      <ul className={styles.key} aria-label="Map key">
        {bands.map((band) => {
          const display = bandDisplay(band);
          return (
            <li key={band}>
              <BandSwatch pattern={display.pattern} />
              <span>
                <strong>{display.label}</strong>
                {display.chanceEachYear && (
                  <span className={styles.chance}> {display.chanceEachYear} chance each year</span>
                )}
              </span>
            </li>
          );
        })}
        {noData && (
          <li>
            <BandSwatch pattern="other" />
            <span>
              <strong>No data</strong>
              <span className={styles.chance}>
                {" "}
                Not mapped, so this area can&apos;t be called clear
              </span>
            </span>
          </li>
        )}
        <li>
          <svg className={styles.circle} viewBox="0 0 28 28" aria-hidden="true" focusable="false">
            <circle cx="14" cy="14" r="11" />
          </svg>
          <span>
            <strong>Search area</strong>
            <span className={styles.chance}> {area} around the checked spot</span>
          </span>
        </li>
      </ul>
    </div>
  );
}
