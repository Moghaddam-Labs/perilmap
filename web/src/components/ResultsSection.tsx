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
