"use client";

import { forwardRef } from "react";
import type { Assessment } from "@/lib/api/types";
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
          </>
        )}
      </section>
    );
  },
);
