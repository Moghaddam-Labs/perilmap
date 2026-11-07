import { bandDisplay } from "@/lib/bands";
import type { NearestZones } from "@/lib/api/types";
import { BandSwatch } from "./BandSwatch";
import styles from "./NearestZonesTable.module.css";

const METRES = new Intl.NumberFormat("en-GB");

/** The nearest zone of each level, using the API's own wording for each distance. */
export function NearestZonesTable({ measurement }: { measurement: NearestZones }) {
  return (
    <table className={styles.table}>
      <caption className={styles.caption}>
        Nearest zone of each level, searching up to{" "}
        {METRES.format(measurement.search_radius_metres)} m from the pin
      </caption>
      <thead className="visually-hidden">
        <tr>
          <th scope="col">Level</th>
          <th scope="col">Nearest zone</th>
        </tr>
      </thead>
      <tbody>
        {measurement.zones.map((zone) => {
          const band = bandDisplay(zone.band);
          return (
            <tr key={zone.band} data-near={zone.metres === 0 ? "true" : undefined}>
              <th scope="row" className={styles.band}>
                <BandSwatch pattern={band.pattern} />
                {band.label}
              </th>
              <td className={zone.metres === null ? styles.none : undefined}>{zone.label}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
