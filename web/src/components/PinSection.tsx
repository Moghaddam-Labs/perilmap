"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { describePin, isInsideLondon, type Position } from "@/lib/geo";
import { Button } from "./Button";
import { Notice } from "./Notice";
import type { FoundPostcode } from "./PostcodeSearch";
import styles from "./PinSection.module.css";

const LocationMap = dynamic(() => import("./LocationMap").then((module) => module.LocationMap), {
  ssr: false,
  loading: () => <div className={styles.loading}>Loading the map</div>,
});

interface PinSectionProps {
  found: FoundPostcode;
  onConfirm: (pin: Position) => void;
}

/** The second step: putting the pin on the home itself. */
export function PinSection({ found, onConfirm }: PinSectionProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [pin, setPin] = useState<Position>(found);
  const [mapUnavailable, setMapUnavailable] = useState(false);

  useEffect(() => {
    headingRef.current?.focus();
    headingRef.current?.scrollIntoView({ block: "start" });
  }, []);

  const outside = !isInsideLondon(pin);
  return (
    <section className={styles.section} aria-labelledby="mark-the-home">
      <div className={styles.intro}>
        <h2 id="mark-the-home" ref={headingRef} tabIndex={-1}>
          Mark the home on the map
        </h2>
        <p>
          The pin starts at the centre of {found.postcode}. Click or tap the map to move it onto the
          home, or drag it. With a keyboard, select the pin and use the arrow keys.
        </p>
      </div>

      {mapUnavailable ? (
        <Notice title="The map couldn't load">
          The pin stays at the centre of {found.postcode}. You can still check this location, or
          reload the page to try the map again.
        </Notice>
      ) : (
        <LocationMap
          start={found}
          pin={pin}
          onPinChange={setPin}
          onUnavailable={() => setMapUnavailable(true)}
        />
      )}

      <p className={styles.legend}>
        <svg viewBox="0 0 32 8" aria-hidden="true" focusable="false">
          <line x1="1" y1="4" x2="31" y2="4" />
        </svg>
        The dashed line is the edge of Greater London, the area PerilMap covers so far.
      </p>

      <p className={styles.status} aria-live="polite">
        {describePin(pin, found)}
        {outside && " This spot is outside Greater London, so there won't be results for it yet."}
      </p>

      <div className={styles.actions}>
        <Button onClick={() => onConfirm(pin)}>Check this location</Button>
        <Button variant="secondary" onClick={() => setPin(found)}>
          Move the pin back to the centre
        </Button>
      </div>
    </section>
  );
}
