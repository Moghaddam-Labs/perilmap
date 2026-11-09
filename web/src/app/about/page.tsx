import type { Metadata } from "next";
import Link from "next/link";
import { ContentPage, ContentSection } from "@/components/ContentPage";
import styles from "@/components/ContentPage.module.css";
import { ExternalLink } from "@/components/ExternalLink";
import { DISCLAIMER } from "@/components/SiteFooter";
import { DATA_SOURCES } from "@/lib/dataSources";
import { NOT_COVERED } from "@/lib/notCovered";
import { PAGES, PAGES_UPDATED, REPO } from "@/lib/pages";
import { statusDisplay } from "@/lib/status";

export const metadata: Metadata = {
  title: "About the data: PerilMap",
  description:
    "What PerilMap's results can and can't tell you, how they're worked out, and where the data comes from.",
};

/** Each gap label, as it appears on result cards, with what it means. */
const GAPS = [
  ["no_data", "means there's no data for that spot. It says nothing about the risk, either way."],
  [
    "incomplete",
    "means the spot is near the edge of London or near an area with no data, so a nearby zone may not be shown.",
  ],
  [
    "not_available_here",
    "means the spot is outside Greater London, the area PerilMap covers so far.",
  ],
  [
    "temporarily_unavailable",
    "means a check failed this time. It says nothing about the risk, so try again shortly.",
  ],
] as const;

const OFFICIAL_CHECKS = [
  {
    label: "Check your long term flood risk on GOV.UK",
    href: "https://www.gov.uk/check-long-term-flood-risk",
  },
  { label: "Sign up for flood warnings", href: "https://www.gov.uk/sign-up-for-flood-warnings" },
  {
    label: "Swelling and shrinking soils, from the British Geological Survey",
    href: "https://www.bgs.ac.uk/geology-projects/shallow-geohazards/clay-shrink-swell/",
  },
];

export default function AboutPage() {
  return (
    <ContentPage
      title="About the data"
      lead="PerilMap brings together official open data about the area around a home. Here's what it can and can't tell you, and how each result is worked out."
      updated={PAGES_UPDATED}
    >
      <ContentSection id="what-it-is" title="What PerilMap is, and isn't">
        <p className={styles.note}>{DISCLAIMER}</p>
        <p>
          PerilMap shows what official data says about the area around a spot you choose. It
          can&apos;t see the home itself, such as its floor level, its condition or any flood
          protection it has. Insurers, lenders and surveyors use their own data and methods, so
          their view can differ.
        </p>
        <p>
          Each peril gets its own result, with what it means and how sure it is. There&apos;s no
          overall score, because adding different risks together would hide more than it shows.
        </p>
      </ContentSection>

      <ContentSection id="how-results-work" title="How the results are worked out">
        <h3>Flooding from rivers and sea, and from surface water</h3>
        <p>
          The Environment Agency maps four levels of flood risk: High, Medium, Low and Very Low,
          based on the chance of flooding in any one year. PerilMap finds the nearest zone of each
          level within 1 km of the pin.
        </p>
        <ul>
          <li>
            The Environment Agency&apos;s maps are turned into a grid of 5 m squares, so distances
            can read up to about 6 m too close, and &ldquo;on a zone&rdquo; means on it or within
            about 5 m.
          </li>
          <li>
            The zones drawn on the map come from exactly the same squares, with their edges smoothed
            by up to 2.5 m so they don&apos;t look like steps.
          </li>
          <li>
            The Environment Agency says this data estimates risk to an area of land and is generally
            not suitable for assessing one property.
          </li>
        </ul>

        <h3>Summer temperature</h3>
        <p>
          This is the modelled average outdoor air temperature from June to August, day and night,
          for 2018 to 2022, for the neighbourhood around the pin. Temperatures across London only
          vary by about two degrees, so PerilMap shows how the area compares, not a risk rating.
          London&apos;s range and the fifths are PerilMap&apos;s own calculation from this data.
        </p>

        <h3>Clay subsidence</h3>
        <p>
          The free national data is too coarse for any one home, so PerilMap gives general
          information for London instead of a result, and points to a detailed report for a specific
          address.
        </p>
      </ContentSection>

      <ContentSection id="gaps" title="When data is missing">
        <p>A gap in the data is never shown as if the area were clear.</p>
        <ul>
          {GAPS.map(([status, meaning]) => (
            <li key={status}>
              <strong>{statusDisplay(status)?.label}</strong> {meaning}
            </li>
          ))}
        </ul>
      </ContentSection>

      <ContentSection id="not-covered" title="What PerilMap doesn't cover">
        <p>These aren&apos;t checked yet, so a result says nothing about them:</p>
        <ul>
          {NOT_COVERED.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </ContentSection>

      <ContentSection id="sources" title="Where the data comes from">
        <ul className={styles.panel}>
          {DATA_SOURCES.map((source) => (
            <li key={source.label}>
              <h3>
                <ExternalLink href={source.href}>{source.label}</ExternalLink>
              </h3>
              <dl className={styles.facts}>
                <dt>From</dt>
                <dd>{source.publisher}</dd>
                <dt>Updated</dt>
                <dd>{source.updated}</dd>
                <dt>Detail</dt>
                <dd>{source.detail}</dd>
              </dl>
            </li>
          ))}
        </ul>
        <p>
          Every credit and licence is listed at the bottom of each page. Flood, temperature and
          boundary data is used under the Open Government Licence.
        </p>
      </ContentSection>

      <ContentSection id="official-checks" title="Official checks">
        <p>Before making a decision about a home, check the official sources directly:</p>
        <ul>
          {OFFICIAL_CHECKS.map((check) => (
            <li key={check.href}>
              <ExternalLink href={check.href}>{check.label}</ExternalLink>
            </li>
          ))}
          <li>
            <Link href={PAGES.floodInsurance.href}>{PAGES.floodInsurance.label}</Link>, for help
            finding home insurance near a flood zone
          </li>
        </ul>
      </ContentSection>

      <ContentSection id="corrections" title="Spotted a mistake?">
        <p>
          PerilMap tries to stay as close to its sources as possible. If something looks wrong,{" "}
          <ExternalLink href={`${REPO}/issues`}>report it on GitHub</ExternalLink>.
        </p>
      </ContentSection>
    </ContentPage>
  );
}
