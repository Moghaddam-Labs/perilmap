import { ExternalLink } from "./ExternalLink";
import styles from "./SiteFooter.module.css";

/** Matches the wording the API sends with every result. */
export const DISCLAIMER =
  "Guidance only. This is not an insurance quote, survey or financial advice. It describes the area around a home, not the home itself.";

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <p className={styles.disclaimer}>{DISCLAIMER}</p>
        <p>
          The map on the home page is drawn from the Environment Agency&apos;s Risk of Flooding from
          Rivers and Sea data, under the{" "}
          <ExternalLink href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">
            Open Government Licence v3.0
          </ExternalLink>
          . © Environment Agency copyright and/or database right 2025. All rights reserved.
        </p>
        <p>
          Created by{" "}
          <ExternalLink href="https://shazmoghaddam.github.io/">Shaz Moghaddam</ExternalLink>,
          London. A Moghaddam Labs project.
        </p>
      </div>
    </footer>
  );
}
