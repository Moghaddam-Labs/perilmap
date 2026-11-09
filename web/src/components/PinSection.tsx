"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { ApiError, assessLocation, fetchZoneMap, type ApiProblem } from "@/lib/api/client";
import type { Assessment } from "@/lib/api/types";
import { describePin, distanceMetres, isInsideLondon, type Position } from "@/lib/geo";
import { FLOOD_MAP_LAYERS } from "@/lib/zoneMap";
import { Button } from "./Button";
import type { ZoneOverlay } from "./LocationMap";
import { Notice } from "./Notice";
import type { FoundPostcode } from "./PostcodeSearch";
import { ResultsSection } from "./ResultsSection";
import { NO_LAYER, ZoneMapControls, type ZoneMapState } from "./ZoneMapControls";
import styles from "./PinSection.module.css";

const LocationMap = dynamic(() => import("./LocationMap").then((module) => module.LocationMap), {
  ssr: false,
  loading: () => <div className={styles.loading}>Loading the map</div>,
});

const PROBLEMS: Record<ApiProblem, string> = {
  invalid: "That location couldn't be checked. Move the pin and try again.",
  not_found: "That location couldn't be checked. Move the pin and try again.",
  busy: "There have been too many checks in a short time. Wait a minute, then try again.",
  unavailable: "Results aren't available right now. Try again in a few minutes.",
};

const ZONE_PROBLEMS: Record<ApiProblem, string> = {
  invalid: "The flood zones couldn't be drawn for this spot.",
  not_found: "The flood zones couldn't be drawn for this spot.",
  busy: "The flood zones couldn't load, because there have been too many checks in a short time.",
  unavailable: "The flood zones couldn't load.",
};

const DEFAULT_RADIUS_METRES = 1_000;

interface Checked {
  id: number;
  pin: Position;
  assessment: Assessment;
  at: Date;
}

/** The flood checks that have results here, so their zones can be drawn. */
function drawableLayers(assessment: Assessment) {
  return FLOOD_MAP_LAYERS.filter((layer) =>
    assessment.results.some(
      (result) => result.peril_id === layer.perilId && result.status !== "not_available_here",
    ),
  );
}

function searchRadius(assessment: Assessment) {
  for (const result of assessment.results) {
    if (result.measurement?.type === "nearest_zones")
      return result.measurement.search_radius_metres;
  }
  return DEFAULT_RADIUS_METRES;
}

const CHECKED_AT = new Intl.DateTimeFormat("en-GB", { dateStyle: "long", timeStyle: "short" });

/** The second and third steps: putting the pin on the home, then checking what's around it. */
export function PinSection({ found }: { found: FoundPostcode }) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  const resultsRef = useRef<HTMLHeadingElement>(null);
  const requestRef = useRef<AbortController | null>(null);
  const [pin, setPin] = useState<Position>(found);
  const [mapUnavailable, setMapUnavailable] = useState(false);
  const [checking, setChecking] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [checked, setChecked] = useState<Checked | null>(null);
  const [layer, setLayer] = useState<string>(FLOOD_MAP_LAYERS[0]?.perilId ?? NO_LAYER);
  const [zoneMaps, setZoneMaps] = useState<Record<string, ZoneMapState>>({});
  const checkCount = useRef(0);
  const zoneRequests = useRef<AbortController[]>([]);

  function cancelZoneRequests() {
    for (const request of zoneRequests.current) request.abort();
    zoneRequests.current = [];
  }

  useEffect(
    () => () => {
      requestRef.current?.abort();
      cancelZoneRequests();
    },
    [],
  );

  // Results get their own heading, so focus moves there once they arrive.
  useEffect(() => {
    if (checked) {
      resultsRef.current?.focus();
      resultsRef.current?.scrollIntoView({ block: "start" });
    }
  }, [checked]);

  async function check() {
    requestRef.current?.abort();
    const request = new AbortController();
    requestRef.current = request;
    const spot = pin;
    setProblem(null);
    setChecking(true);
    try {
      const assessment = await assessLocation(spot, request.signal);
      checkCount.current += 1;
      const record = { id: checkCount.current, pin: spot, assessment, at: new Date() };
      cancelZoneRequests();
      setZoneMaps({});
      setChecked(record);
      if (drawableLayers(assessment).some((choice) => choice.perilId === layer)) {
        loadZones(record, layer);
      }
    } catch (caught) {
      if (request.signal.aborted) return;
      setProblem(PROBLEMS[caught instanceof ApiError ? caught.problem : "unavailable"]);
    } finally {
      if (requestRef.current === request) setChecking(false);
    }
  }

  const layers = useMemo(() => (checked ? drawableLayers(checked.assessment) : []), [checked]);
  const shownLayer = layers.some((choice) => choice.perilId === layer) ? layer : NO_LAYER;
  const zoneState = shownLayer === NO_LAYER ? null : (zoneMaps[shownLayer] ?? null);

  const radiusMetres = checked ? searchRadius(checked.assessment) : DEFAULT_RADIUS_METRES;
  const overlay = useMemo<ZoneOverlay | null>(
    () =>
      checked && layers.length
        ? {
            checkId: checked.id,
            centre: checked.pin,
            radiusMetres,
            zoneMap: zoneState?.status === "ready" ? zoneState.zoneMap : null,
          }
        : null,
    [checked, layers.length, radiusMetres, zoneState],
  );

  /** Fetches one layer's zones for a check. Once loaded, they're kept until the next check. */
  function loadZones(spot: Checked, perilId: string) {
    if (perilId === NO_LAYER) return;
    const request = new AbortController();
    zoneRequests.current.push(request);
    setZoneMaps((maps) => ({ ...maps, [perilId]: { status: "loading" } }));
    fetchZoneMap(spot.pin, perilId, request.signal)
      .then((zoneMap) =>
        setZoneMaps((maps) => ({ ...maps, [perilId]: { status: "ready", zoneMap } })),
      )
      .catch((caught: unknown) => {
        if (request.signal.aborted) return;
        const problem = caught instanceof ApiError ? caught.problem : "unavailable";
        setZoneMaps((maps) => ({
          ...maps,
          [perilId]: { status: "failed", message: ZONE_PROBLEMS[problem] },
        }));
      });
  }

  function chooseLayer(perilId: string) {
    setLayer(perilId);
    const state = zoneMaps[perilId];
    if (checked && (!state || state.status === "failed")) loadZones(checked, perilId);
  }

  useEffect(() => {
    headingRef.current?.focus();
    headingRef.current?.scrollIntoView({ block: "start" });
  }, []);

  const outside = !isInsideLondon(pin);
  return (
    <section className={styles.section} aria-labelledby="mark-the-home">
      {checked && (
        <div className={`print-only ${styles.report}`}>
          <p className={styles.reportTitle}>PerilMap report</p>
          <p>
            Near {found.postcode}. {describePin(checked.pin, found)}
          </p>
          <p>
            Latitude {checked.pin.latitude.toFixed(5)}, longitude {checked.pin.longitude.toFixed(5)}
            . Checked on {CHECKED_AT.format(checked.at)}.
          </p>
        </div>
      )}

      <div className={`${styles.intro} no-print`}>
        <h2 id="mark-the-home" ref={headingRef} tabIndex={-1}>
          Mark the home on the map
        </h2>
        <p>
          The pin starts at the centre of {found.postcode}. Click or tap the map to move it onto the
          home, or drag it. With a keyboard, select the pin and use the arrow keys.
        </p>
      </div>

      {mapUnavailable ? (
        <Notice title="The map couldn't load" className="no-print">
          The pin stays at the centre of {found.postcode}. You can still check this location, or
          reload the page to try the map again.
        </Notice>
      ) : (
        <LocationMap
          start={found}
          pin={pin}
          overlay={overlay}
          onPinChange={setPin}
          onUnavailable={() => setMapUnavailable(true)}
        />
      )}

      {checked && layers.length > 0 && !mapUnavailable && (
        <ZoneMapControls
          layers={layers}
          chosen={shownLayer}
          state={zoneState}
          radiusMetres={radiusMetres}
          stale={distanceMetres(checked.pin, pin) > 1}
          onChoose={chooseLayer}
          onRetry={() => checked && loadZones(checked, shownLayer)}
        />
      )}

      <p className={`${styles.legend} no-print`}>
        <svg viewBox="0 0 32 8" aria-hidden="true" focusable="false">
          <line x1="1" y1="4" x2="31" y2="4" />
        </svg>
        The dashed line is the edge of Greater London, the area PerilMap covers so far.
      </p>

      <p className={`${styles.status} no-print`} aria-live="polite">
        {describePin(pin, found)}
        {outside && " This spot is outside Greater London, so there won't be results for it yet."}
      </p>

      <div className={`${styles.actions} no-print`}>
        <Button onClick={check} disabled={checking}>
          {checking ? "Checking" : "Check this location"}
        </Button>
        <Button variant="secondary" onClick={() => setPin(found)}>
          Move the pin back to the centre
        </Button>
      </div>
      <p className="visually-hidden" role="status">
        {checking ? "Checking this location" : ""}
      </p>

      {problem && (
        <Notice title="We couldn't check this location" tone="error" className="no-print">
          {problem}
        </Notice>
      )}

      {checked && (
        <ResultsSection
          ref={resultsRef}
          assessment={checked.assessment}
          postcode={found.postcode}
          stale={distanceMetres(checked.pin, pin) > 1}
        />
      )}
    </section>
  );
}
