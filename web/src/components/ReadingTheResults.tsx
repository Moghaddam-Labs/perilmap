import { DATA_SOURCES } from "@/lib/dataSources";
import { FLOOD_BANDS } from "@/lib/bands";
import { BandSwatch } from "./BandSwatch";
import { ExplainerCards, type Explainer } from "./ExplainerCards";
import { ExternalLink } from "./ExternalLink";
import { StatusBadge } from "./StatusBadge";
import styles from "./ReadingTheResults.module.css";

const GAPS = [
  { status: "no_data", text: "The data has a blank here, so we can't say anything." },
  { status: "incomplete", text: "A gap in the data is close enough to affect this result." },
  { status: "not_available_here", text: "This spot is outside the areas PerilMap covers so far." },
  {
    status: "general_information",
    text: "Information for London as a whole, not a result for this spot.",
  },
];

const CARDS: Explainer[] = [
  {
    id: "flood-levels",
    title: "Telling flood levels apart",
    teaser: "The Environment Agency's four levels, each with its own pattern.",
    icon: (
      <>
        {FLOOD_BANDS.map((band) => (
          <BandSwatch key={band.label} pattern={band.pattern} />
        ))}
      </>
    ),
    content: (
      <>
        <p className={styles.intro}>
          Each level has a pattern and a name as well as a colour, so nothing depends on seeing
          colour. The figures are the chance of flooding in any one year.
        </p>
        <ul className={styles.rows}>
          {FLOOD_BANDS.map((band) => (
            <li key={band.label} className={styles.band}>
              <BandSwatch pattern={band.pattern} />
              <span>
                <strong>{band.label}</strong>
                <span className={styles.detail}>{band.chanceEachYear}</span>
              </span>
            </li>
          ))}
        </ul>
      </>
    ),
  },
  {
    id: "gaps",
    title: "A gap never looks safe",
    teaser: "How missing or partial data is labelled.",
    icon: (
      <svg viewBox="0 0 32 32" focusable="false" className={styles.gapIcon}>
        <circle cx="16" cy="16" r="13" strokeDasharray="4 3.5" />
        <path d="M12.5 12.6a3.6 3.6 0 1 1 5.4 3.1c-1.3.8-1.9 1.6-1.9 2.9M16 22.4v.2" />
      </svg>
    ),
    content: (
      <>
        <p className={styles.intro}>
          Missing data is labelled as missing, so it can&apos;t be mistaken for low risk.
        </p>
        <ul className={styles.rows}>
          {GAPS.map(({ status, text }) => (
            <li key={status} className={styles.gap}>
              <StatusBadge status={status} />
              <span className={styles.detail}>{text}</span>
            </li>
          ))}
        </ul>
      </>
    ),
  },
  {
    id: "sources",
    title: "Where the data comes from",
    teaser: "Who publishes each dataset, and how recent it is.",
    icon: (
      <svg viewBox="0 0 32 32" focusable="false" className={styles.gapIcon}>
        <path d="m16 5 11 5.5L16 16 5 10.5 16 5Z" />
        <path d="m5 16 11 5.5L27 16" />
        <path d="m5 21.5 11 5.5 11-5.5" />
      </svg>
    ),
    content: (
      <ul className={styles.rows}>
        {DATA_SOURCES.map((source) => (
          <li key={source.label} className={styles.source}>
            <ExternalLink href={source.href}>{source.label}</ExternalLink>
            <span className={styles.detail}>{source.publisher}</span>
            <span className={styles.detail}>{source.updated}</span>
          </li>
        ))}
      </ul>
    ),
  },
];

export function ReadingTheResults() {
  return (
    <section aria-labelledby="reading-the-results">
      <h2 id="reading-the-results">Reading the results</h2>
      <p className={styles.lead}>Open a card for the details.</p>
      <ExplainerCards cards={CARDS} />
    </section>
  );
}
