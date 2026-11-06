import { BandKey } from "@/components/BandKey";
import { LocationFinder } from "@/components/LocationFinder";
import { PerilIcon } from "@/components/PerilIcon";
import { StatusBadge } from "@/components/StatusBadge";
import styles from "./page.module.css";

const PERILS = [
  {
    perilId: "flood_rivers_and_sea",
    title: "Flooding",
    text: "How close the nearest Environment Agency flood zones are, for rivers and the sea, and for surface water.",
  },
  {
    perilId: "heat",
    title: "Summer heat",
    text: "How an area's modelled average summer temperature compares across London.",
  },
  {
    perilId: "subsidence",
    title: "Ground movement",
    text: "What clay soils can mean for homes in London, and how to get a report for a specific home.",
  },
];

const STEPS = [
  { title: "Find your postcode", text: "This takes the map to the right area." },
  { title: "Mark the home on the map", text: "A pin is more exact than a postcode alone." },
  {
    title: "Read each result",
    text: "Each one says what it means, how sure it is and what you can do next.",
  },
];

const GAPS = [
  { status: "no_data", text: "The data has a blank here, so we can't say anything." },
  { status: "incomplete", text: "A gap in the data is close enough to affect this result." },
  { status: "not_available_here", text: "This spot is outside the areas PerilMap covers so far." },
];

export default function HomePage() {
  return (
    <main id="main">
      <LocationFinder />

      <div className={styles.content}>
        <section aria-labelledby="what-it-looks-at">
          <h2 id="what-it-looks-at">What PerilMap looks at</h2>
          <ul className={styles.perils}>
            {PERILS.map(({ perilId, title, text }) => (
              <li key={perilId}>
                <PerilIcon perilId={perilId} />
                <h3>{title}</h3>
                <p>{text}</p>
              </li>
            ))}
          </ul>
          <p className={styles.note}>
            Flooding from groundwater, reservoirs, sewers and blocked drains isn&apos;t covered.
            PerilMap covers Greater London so far.
          </p>
        </section>

        <section id="how-it-works" className={styles.split} aria-labelledby="how-it-works-title">
          <div>
            <h2 id="how-it-works-title">How it works</h2>
            <p className={styles.intro}>
              You don&apos;t need an account, and your search isn&apos;t saved.
            </p>
          </div>
          <ol className={styles.steps}>
            {STEPS.map(({ title, text }) => (
              <li key={title}>
                <h3>{title}</h3>
                <p>{text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className={styles.split} aria-labelledby="flood-levels">
          <div>
            <h2 id="flood-levels">Flood levels you can tell apart</h2>
            <p className={styles.intro}>
              These are the Environment Agency&apos;s own levels. Each has a pattern and a name as
              well as a colour, so nothing depends on seeing colour. The figures are the chance of
              flooding in any one year.
            </p>
          </div>
          <BandKey />
        </section>

        <section className={styles.split} aria-labelledby="gaps">
          <div>
            <h2 id="gaps">A gap never looks safe</h2>
            <p className={styles.intro}>
              Missing data is labelled as missing, so it can&apos;t be mistaken for low risk.
            </p>
          </div>
          <ul className={styles.gaps}>
            {GAPS.map(({ status, text }) => (
              <li key={status}>
                <StatusBadge status={status} />
                <p>{text}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
