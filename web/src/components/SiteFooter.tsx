import type { ReactNode } from "react";
import { BrandMark } from "./BrandMark";
import { ExternalLink } from "./ExternalLink";
import styles from "./SiteFooter.module.css";

/** Matches the wording the API sends with every result. A test keeps the two the same. */
export const DISCLAIMER =
  "Guidance only. This is not an insurance quote, survey or financial advice. It describes the area around a home, not the home itself.";

const REPO = "https://github.com/Moghaddam-Labs/perilmap";
const OGL_V3 = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/";
const OGL_V2 = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/";

const DATA_SOURCES = [
  {
    label: "Rivers and sea flood zones",
    publisher: "Environment Agency",
    href: "https://www.data.gov.uk/dataset/943d2bbb-aa08-45d1-96cb-42556cd01d94/risk-of-flooding-from-rivers-and-sea2",
  },
  {
    label: "Surface water flood zones",
    publisher: "Environment Agency",
    href: "https://www.data.gov.uk/dataset/risk-of-flooding-from-surface-water3",
  },
  {
    label: "Summer air temperature",
    publisher: "Greater London Authority, Bloomberg Associates and Arup",
    href: "https://data.london.gov.uk/dataset/climate-risk-mapping",
  },
  {
    label: "Ground movement",
    publisher: "British Geological Survey",
    href: "https://www.bgs.ac.uk/datasets/bgs-geosure-5-km-hex-grid/",
  },
  { label: "Postcode lookup", publisher: "postcodes.io", href: "https://postcodes.io/" },
];

const PROJECT_LINKS = [
  { label: "Source code", href: REPO },
  { label: "Licence", href: `${REPO}/blob/main/LICENSE` },
  { label: "Security policy", href: `${REPO}/blob/main/SECURITY.md` },
  { label: "Contributing", href: `${REPO}/blob/main/CONTRIBUTING.md` },
  { label: "Changelog", href: `${REPO}/blob/main/CHANGELOG.md` },
];

function FooterColumn({
  title,
  id,
  children,
}: {
  title: string;
  id?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className={styles.column}>
      <h2 className={styles.heading}>{title}</h2>
      {children}
    </section>
  );
}

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.columns}>
          <div className={styles.about}>
            <p className={styles.wordmark}>
              <BrandMark />
              PerilMap
            </p>
            <p className={styles.disclaimer}>{DISCLAIMER}</p>
          </div>

          <FooterColumn title="Data sources">
            <ul className={styles.list}>
              {DATA_SOURCES.map(({ label, publisher, href }) => (
                <li key={label}>
                  <ExternalLink href={href}>{label}</ExternalLink>
                  <span className={styles.detail}>{publisher}</span>
                </li>
              ))}
            </ul>
          </FooterColumn>

          <FooterColumn title="Project">
            <ul className={styles.list}>
              {PROJECT_LINKS.map(({ label, href }) => (
                <li key={label}>
                  <ExternalLink href={href}>{label}</ExternalLink>
                </li>
              ))}
            </ul>
          </FooterColumn>

          <FooterColumn title="Your privacy" id="privacy">
            <p>
              Searched postcodes and locations aren&apos;t saved, and they&apos;re kept out of web
              addresses and logs. The map comes from OpenFreeMap, which can see which area of the
              map you&apos;re looking at, but not the postcode or the pin.
            </p>
          </FooterColumn>
        </div>

        <div className={styles.credits}>
          <p>
            Flood data and the home page map: © Environment Agency copyright and/or database right
            2025. All rights reserved. Temperature data: Greater London Authority, using Arup&apos;s
            UHeat model. Ground movement information: BGS © UKRI. Contains OS data © Crown copyright
            2020. London boundary: contains National Statistics data and Ordnance Survey data ©
            Crown copyright and database right 2015. Map: OpenFreeMap © OpenMapTiles, data from
            OpenStreetMap © OpenStreetMap contributors.
          </p>
          <p>
            Used under the Open Government Licence:{" "}
            <ExternalLink href={OGL_V3}>version 3.0</ExternalLink> for flood and temperature data,
            and <ExternalLink href={OGL_V2}>version 2.0</ExternalLink> for the London boundary.
          </p>
        </div>

        <div className={styles.bar}>
          <p>
            Designed by{" "}
            <ExternalLink href="https://shazmoghaddam.github.io/">Shaz Moghaddam</ExternalLink>,
            London
          </p>
          <p>© 2026 Shaz Moghaddam. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
