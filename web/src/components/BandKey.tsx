import { FLOOD_BANDS } from "@/lib/bands";
import { BandSwatch } from "./BandSwatch";
import styles from "./BandKey.module.css";

/** The key to the Environment Agency's flood levels, highest first. */
export function BandKey() {
  return (
    <ul className={styles.key}>
      {FLOOD_BANDS.map((band) => (
        <li key={band.label} className={styles.row}>
          <BandSwatch pattern={band.pattern} />
          <span className={styles.name}>{band.label}</span>
          <span className={styles.chance}>{band.chanceEachYear}</span>
        </li>
      ))}
    </ul>
  );
}
