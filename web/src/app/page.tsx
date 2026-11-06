import { BandKey } from "@/components/BandKey";
import { HomeHero } from "@/components/HomeHero";
import { StatusBadge } from "@/components/StatusBadge";
import styles from "./page.module.css";

const ANSWERS = [
  {
    question: "What it means",
    answer: "The result in plain English, using the source's own levels.",
  },
  { question: "How sure it is", answer: "How detailed the data is, and where it could be wrong." },
  { question: "What you can do", answer: "Practical next steps, with links to official guidance." },
];

const GAPS = [
  { status: "no_data", text: "The data has a blank here, so we can't say anything." },
  { status: "incomplete", text: "A gap in the data is close enough to affect this result." },
  { status: "not_available_here", text: "This spot is outside the areas PerilMap covers so far." },
];

export default function HomePage() {
  return (
    <>
      <HomeHero />
      <main id="main" className={styles.main}>
        <section className={styles.section}>
          <h2>Every result answers three questions</h2>
          <dl className={styles.answers}>
            {ANSWERS.map(({ question, answer }) => (
              <div key={question}>
                <dt className={styles.question}>{question}</dt>
                <dd>{answer}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className={styles.split}>
          <div>
            <h2>Flood levels you can tell apart</h2>
            <p className={styles.intro}>
              These are the Environment Agency&apos;s own levels. Each has a pattern and a name as
              well as a colour, so nothing depends on seeing colour. The figures are the chance of
              flooding in any one year.
            </p>
          </div>
          <BandKey />
        </section>

        <section className={styles.split}>
          <div>
            <h2>A gap never looks safe</h2>
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
      </main>
    </>
  );
}
