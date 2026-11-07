"use client";

import { useState } from "react";
import { HomeHero } from "./HomeHero";
import { PinSection } from "./PinSection";
import { PostcodeSearch, type FoundPostcode } from "./PostcodeSearch";

/** Search, the map, then results. Nothing here is saved or added to the web address. */
export function LocationFinder() {
  const [found, setFound] = useState<FoundPostcode | null>(null);
  const [search, setSearch] = useState(0);

  return (
    <>
      <HomeHero
        search={
          <PostcodeSearch
            onFound={(next) => {
              setFound(next);
              setSearch((count) => count + 1);
            }}
          />
        }
      />
      {found && <PinSection key={search} found={found} />}
    </>
  );
}
