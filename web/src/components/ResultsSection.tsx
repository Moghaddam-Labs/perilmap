"use client";

import Link from "next/link";
import { forwardRef } from "react";
import type { Assessment } from "@/lib/api/types";
import { PAGES } from "@/lib/pages";
import { printPage } from "@/lib/print";
import { Button } from "./Button";
import { Notice } from "./Notice";
import { ResultCard } from "./ResultCard";
import styles from "./ResultsSection.module.css";

interface ResultsSectionProps {
  assessment: Assessment;
  postcode: string;
  stale: boolean;
}

/** How recent each result's data is, so freshness shows without opening a card. */
function DataDates({ assessment }: { assessment: Assessment }) {
  const dates = assessment.results.flatMap((result) =>
    result.sources
      .filter((source) => source.last_updated)
      .slice(0, 1)
      .map((source) => ({ title: result.title, updated: source.last_updated })),
  );
  if (dates.length === 0) return null;
  return (
    <div className={styles.dates}>
      <h3>How recent the data is</h3>
      <dl>
        {dates.map(({ title, updated }) => (
          <div key={title}>
            <dt>{title}</dt>
            <dd>{updated}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/** True when any flood check found a zone within its search area. */
function nearFloodZone(assessment: Assessment) {
  return assessment.results.some(
    (result) =>
      result.measurement?.type === "nearest_zones" &&
      result.measurement.zones.some((zone) => zone.metres !== null),
  );
}

/** Everything the API found around the pin, or why it couldn't say. */
export const ResultsSection = forwardRef<HTMLHeadingElement, ResultsSectionProps>(
  function ResultsSection({ assessment, postcode, stale }, headingRef) {
    return (
      <section className={styles.section} aria-labelledby="results-title">
        <h2 id="results-title" ref={headingRef} tabIndex={-1}>
          {assessment.available_here
            ? `What's around the pin near ${postcode}`
            : "Not available here yet"}
        </h2>

        {stale && (
          <Notice title="You've moved the pin">
            These results are for where the pin was before. Check this location again to update
            them.
          </Notice>
        )}

        {!assessment.available_here ? (
          <p className={styles.intro}>
            {assessment.message ? `${assessment.message}. ` : ""}PerilMap covers Greater London so
            far. Move the pin inside the dashed line on the map to see results.
          </p>
        ) : (
          <>
            <p className={styles.disclaimer}>{assessment.disclaimer}</p>
            <DataDates assessment={assessment} />
            {/* Out of date results aren't offered for printing, so a printout always matches the pin. */}
            {!stale && (
              <Button
                variant="secondary"
                className={`${styles.print} no-print`}
                onClick={() => printPage(`PerilMap report near ${postcode}`)}
              >
                Print or save as PDF
              </Button>
            )}
            <div className={styles.grid}>
              {assessment.results.map((result) => (
                <ResultCard key={result.peril_id} result={result} />
              ))}
            </div>
            {assessment.not_covered.length > 0 && (
              <div className={styles.notCovered}>
                <h3>Not covered</h3>
                <p>
                  PerilMap doesn&apos;t look at these yet, so a result here says nothing about them:
                </p>
                <ul>
                  {assessment.not_covered.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className={styles.further}>
              <h3>Find out more</h3>
              <ul>
                <li>
                  <Link href={PAGES.about.href}>{PAGES.about.label}</Link>: how these results are
                  worked out, and what they can&apos;t tell you
                </li>
                {nearFloodZone(assessment) && (
                  <li>
                    <Link href={PAGES.floodInsurance.href}>{PAGES.floodInsurance.label}</Link>: help
                    finding home insurance near a flood zone
                  </li>
                )}
              </ul>
            </div>
          </>
        )}
      </section>
    );
  },
);
