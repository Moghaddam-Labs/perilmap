"use client";

import { useState } from "react";
import type { Position } from "@/lib/geo";
import { HomeHero } from "./HomeHero";
import { Notice } from "./Notice";
import { PinSection } from "./PinSection";
import { PostcodeSearch, type FoundPostcode } from "./PostcodeSearch";
import styles from "./LocationFinder.module.css";

/** Search, then the map. Nothing here is saved or added to the web address. */
export function LocationFinder() {
  const [found, setFound] = useState<FoundPostcode | null>(null);
  const [search, setSearch] = useState(0);
  const [checked, setChecked] = useState<Position | null>(null);

  return (
    <>
      <HomeHero
        search={
          <PostcodeSearch
            onFound={(next) => {
              setFound(next);
              setChecked(null);
              setSearch((count) => count + 1);
            }}
          />
        }
      />
      {found && <PinSection key={search} found={found} onConfirm={(pin) => setChecked(pin)} />}
      {checked && (
        <div className={styles.next}>
          <Notice title="Results are on their way">
            The results for this location will show here in the next update to PerilMap.
          </Notice>
        </div>
      )}
    </>
  );
}
