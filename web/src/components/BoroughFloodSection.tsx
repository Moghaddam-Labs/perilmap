import data from "@/lib/borough-flood.json";
import { BoroughFloodChart } from "./BoroughFloodChart";
import styles from "./BoroughFloodSection.module.css";

interface Borough {
  name: string;
  code: string;
  low_or_higher_percent: number;
  very_low_percent: number;
}

const BOROUGHS = data.boroughs as Borough[];
const PERCENT = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});

// The example in the text comes from the data, so it can't go out of date when the data changes.
const DEFENDED_EXAMPLE = [...BOROUGHS]
  .filter((borough) => borough.low_or_higher_percent < 1)
  .sort((a, b) => b.very_low_percent - a.very_low_percent)[0];

/** A permanent picture of river and sea flooding across London, the same for every visitor. */
export function BoroughFloodSection() {
  return (
    <section className={styles.section} aria-labelledby="boroughs-title">
      <div className={styles.text}>
        <div className={styles.intro}>
          <h2 id="boroughs-title">Flood zones across London&apos;s boroughs</h2>
          <p className={styles.lead}>
            How much of each borough&apos;s land is in a rivers and sea flood zone. Blue is land the
            Environment Agency rates Low, Medium or High. Grey is land it rates Very Low.
          </p>
        </div>
        <div className={styles.details}>
          {DEFENDED_EXAMPLE && (
            <p>
              A small blue share doesn&apos;t mean no risk. {DEFENDED_EXAMPLE.name} has{" "}
              {PERCENT.format(DEFENDED_EXAMPLE.low_or_higher_percent)}% of its land rated Low or
              higher, but {PERCENT.format(DEFENDED_EXAMPLE.very_low_percent)}% rated Very Low,
              mostly because flood defences such as the Thames Barrier reduce the chance of
              flooding.
            </p>
          )}
          <p>
            This covers rivers and the sea only. Surface water flooding, from heavy rain, can happen
            in every borough.
          </p>
          <p className={styles.note}>
            PerilMap&apos;s own calculation from the Environment Agency&apos;s Risk of Flooding from
            Rivers and Sea data, on a 5 m grid, with borough boundaries from the London Datastore.
            The River Thames itself isn&apos;t counted. Boroughs are in order of their Low or higher
            share.
          </p>
        </div>
      </div>

      <div className={styles.figure}>
        <BoroughFloodChart boroughs={BOROUGHS} />
        <details className={styles.table}>
          <summary>Show the figures as a table</summary>
          <table>
            <caption className="visually-hidden">
              Share of each borough&apos;s land in rivers and sea flood zones
            </caption>
            <thead>
              <tr>
                <th scope="col">Borough</th>
                <th scope="col">Low, Medium or High</th>
                <th scope="col">Very Low</th>
              </tr>
            </thead>
            <tbody>
              {BOROUGHS.map((borough) => (
                <tr key={borough.code}>
                  <th scope="row">{borough.name}</th>
                  <td>{PERCENT.format(borough.low_or_higher_percent)}%</td>
                  <td>{PERCENT.format(borough.very_low_percent)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      </div>
    </section>
  );
}
