import { BoroughFloodSection } from "@/components/BoroughFloodSection";
import { LocationFinder } from "@/components/LocationFinder";
import { PerilIcon } from "@/components/PerilIcon";
import { ReadingTheResults } from "@/components/ReadingTheResults";
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

export default function HomePage() {
  return (
    <main id="main">
      <LocationFinder />

      <div className={styles.content}>
        <BoroughFloodSection />

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

        <section id="how-it-works" aria-labelledby="how-it-works-title">
          <h2 id="how-it-works-title">How it works</h2>
          <p className={styles.intro}>
            You don&apos;t need an account, and your search isn&apos;t saved.
          </p>
          <ol className={styles.steps}>
            {STEPS.map(({ title, text }) => (
              <li key={title}>
                <h3>{title}</h3>
                <p>{text}</p>
              </li>
            ))}
          </ol>
        </section>

        <ReadingTheResults />
      </div>
    </main>
  );
}
