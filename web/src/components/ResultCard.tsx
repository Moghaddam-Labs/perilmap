import type { PerilResult } from "@/lib/api/types";
import { ExternalLink } from "./ExternalLink";
import { NearestZonesTable } from "./NearestZonesTable";
import { PerilIcon } from "./PerilIcon";
import { StatusBadge } from "./StatusBadge";
import { TemperatureGauge } from "./TemperatureGauge";
import styles from "./ResultCard.module.css";

function Measurement({ result }: { result: PerilResult }) {
  const measurement = result.measurement;
  if (!measurement) return null;
  if (measurement.type === "nearest_zones") {
    return <NearestZonesTable measurement={measurement} />;
  }
  return (
    <div className={styles.comparison}>
      <TemperatureGauge
        value={measurement.value}
        low={measurement.range_low}
        high={measurement.range_high}
        unit={measurement.unit}
        group={measurement.group}
      />
      <p className={styles.note}>{measurement.calculation_note}</p>
    </div>
  );
}

/** One peril's result. All the wording comes from the API, so it stays close to the source. */
export function ResultCard({ result }: { result: PerilResult }) {
  const headingId = `result-${result.peril_id}`;
  return (
    <article className={styles.card} aria-labelledby={headingId}>
      <header className={styles.header}>
        <PerilIcon perilId={result.peril_id} />
        <h3 id={headingId}>{result.title}</h3>
        <StatusBadge status={result.status} />
      </header>

      <p className={styles.summary}>{result.summary}</p>

      <Measurement result={result} />

      <section className={styles.part}>
        <h4>What this means</h4>
        <p>{result.what_this_means}</p>
      </section>

      <section className={styles.part}>
        <h4>How sure this is</h4>
        <p>{result.how_sure}</p>
        {result.caveats.length > 0 && (
          <ul className={styles.caveats}>
            {result.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        )}
      </section>

      {(result.what_you_can_do.length > 0 || result.links.length > 0) && (
        <section className={styles.part}>
          <h4>What you can do</h4>
          <ul className={styles.actions}>
            {result.what_you_can_do.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
          {result.links.length > 0 && (
            <ul className={styles.links}>
              {result.links.map((link) => (
                <li key={link.url}>
                  <ExternalLink href={link.url}>{link.label}</ExternalLink>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {result.sources.length > 0 && (
        <details className={styles.sources} data-print-open>
          <summary>About this data</summary>
          {result.sources.map((source) => (
            <dl key={source.name} className={styles.source}>
              <dt>Source</dt>
              <dd>
                {source.url ? (
                  <ExternalLink href={source.url}>{source.name}</ExternalLink>
                ) : (
                  source.name
                )}
                , {source.publisher}
              </dd>
              {source.last_updated && (
                <>
                  <dt>Updated</dt>
                  <dd>{source.last_updated}</dd>
                </>
              )}
              {source.resolution && (
                <>
                  <dt>Detail</dt>
                  <dd>{source.resolution}</dd>
                </>
              )}
              <dt>Licence</dt>
              <dd>{source.licence}</dd>
              <dt>Credit</dt>
              <dd>{source.attribution}</dd>
            </dl>
          ))}
        </details>
      )}
    </article>
  );
}
