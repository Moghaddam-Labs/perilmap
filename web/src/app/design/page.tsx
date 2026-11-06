import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { BandKey } from "@/components/BandKey";
import { BandSwatch } from "@/components/BandSwatch";
import { BrandMark } from "@/components/BrandMark";
import { Button } from "@/components/Button";
import { ExternalLink } from "@/components/ExternalLink";
import { Notice } from "@/components/Notice";
import { StatusBadge } from "@/components/StatusBadge";
import { TextField } from "@/components/TextField";
import { isDesignPageEnabled } from "@/lib/config";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Design system: PerilMap",
  robots: { index: false, follow: false },
};

const STATUSES = [
  "incomplete",
  "general_information",
  "no_data",
  "not_available_here",
  "temporarily_unavailable",
  "a_new_status",
];

const COLOURS = [
  "paper",
  "surface",
  "ink",
  "ink-soft",
  "line",
  "control-edge",
  "link",
  "error",
  "brand-deep",
  "brand-coral",
];

const SWATCH_CLASSES: Record<string, string | undefined> = Object.fromEntries(
  COLOURS.map((name) => [name, styles[`colour-${name}`]]),
);

export default function DesignPage() {
  if (!isDesignPageEnabled()) {
    notFound();
  }
  return (
    <main id="main" className={styles.main}>
      <h1>
        <BrandMark /> Design system
      </h1>

      <section>
        <h2>Type</h2>
        <p className={styles.display}>See the risks around a home</p>
        <h3>Flooding from surface water</h3>
        <p className={styles.body}>
          Body text uses Atkinson Hyperlegible Next, designed by the Braille Institute so that
          similar letters and numbers are easy to tell apart: Il1 O0 5S 8B. The nearest zone is 120
          m away.
        </p>
      </section>

      <section>
        <h2>Colour</h2>
        <ul className={styles.colours}>
          {COLOURS.map((name) => (
            <li key={name}>
              <span className={`${styles.colour} ${SWATCH_CLASSES[name] ?? ""}`} />
              {name}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Flood levels</h2>
        <BandKey />
        <p className={styles.row}>
          <BandSwatch pattern="other" /> A band from a future plug-in, shown under its own name
        </p>
      </section>

      <section>
        <h2>Result statuses</h2>
        <ul className={styles.statuses}>
          {STATUSES.map((status) => (
            <li key={status}>
              <StatusBadge status={status} />
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Controls</h2>
        <div className={styles.controls}>
          <TextField
            label="Postcode"
            hint="For example, SW1A 1AA"
            name="postcode-a"
            autoComplete="off"
          />
          <TextField
            label="Postcode"
            error="Enter a full UK postcode, such as SW1A 1AA."
            name="postcode-b"
            defaultValue="SW1"
            autoComplete="off"
          />
          <p className={styles.row}>
            <Button>Find postcode</Button>
            <Button variant="secondary">Change location</Button>
            <Button disabled>Finding</Button>
          </p>
          <p>
            <ExternalLink href="https://www.gov.uk/check-long-term-flood-risk">
              Check long term flood risk on GOV.UK
            </ExternalLink>
          </p>
        </div>
      </section>

      <section className={styles.notices}>
        <h2>Notices</h2>
        <Notice title="This postcode isn't in London">
          PerilMap covers Greater London so far.
        </Notice>
        <Notice title="We couldn't get this result" tone="error">
          Try again in a moment.
        </Notice>
      </section>
    </main>
  );
}
