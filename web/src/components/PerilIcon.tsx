import type { ReactNode } from "react";
import styles from "./PerilIcon.module.css";

const ICONS: Record<string, ReactNode> = {
  // Two waves under a roof: water reaching a home
  flood_rivers_and_sea: (
    <>
      <path d="M5 11.5 12 5l7 6.5" />
      <path d="M3 15.5c1.5 0 1.5 1.2 3 1.2s1.5-1.2 3-1.2 1.5 1.2 3 1.2 1.5-1.2 3-1.2 1.5 1.2 3 1.2 1.5-1.2 3-1.2" />
      <path d="M3 20c1.5 0 1.5 1.2 3 1.2S7.5 20 9 20s1.5 1.2 3 1.2S13.5 20 15 20s1.5 1.2 3 1.2S19.5 20 21 20" />
    </>
  ),
  // Rain falling on to a puddle
  flood_surface_water: (
    <>
      <path d="M12 3s4.5 4.8 4.5 8a4.5 4.5 0 0 1-9 0c0-3.2 4.5-8 4.5-8Z" />
      <path d="M3 20c1.5 0 1.5 1.2 3 1.2S7.5 20 9 20s1.5 1.2 3 1.2S13.5 20 15 20s1.5 1.2 3 1.2S19.5 20 21 20" />
    </>
  ),
  // A sun
  heat: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3 7 7M17 17l1.7 1.7M5.3 18.7 7 17M17 7l1.7-1.7" />
    </>
  ),
  // The ground's surface, split by a crack running down through it
  subsidence: (
    <>
      <path d="M2.5 7h19" />
      <path d="m12 7-2.5 4 4.5 2.5-3.5 3.5 1.5 4" />
    </>
  ),
};

// A map pin, for a peril added by a future plug-in, so the card still has an icon.
const FALLBACK: ReactNode = (
  <>
    <path d="M12 21.5s7-6.3 7-11.5a7 7 0 1 0-14 0c0 5.2 7 11.5 7 11.5Z" />
    <circle cx="12" cy="10" r="2.5" />
  </>
);

export function hasPerilIcon(perilId: string) {
  return Object.hasOwn(ICONS, perilId);
}

/** Decorative, so always put the peril's name in text beside it. */
export function PerilIcon({ perilId }: { perilId: string }) {
  return (
    <svg className={styles.icon} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      {hasPerilIcon(perilId) ? ICONS[perilId] : FALLBACK}
    </svg>
  );
}
