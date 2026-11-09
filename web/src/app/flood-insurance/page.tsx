import type { Metadata } from "next";
import Link from "next/link";
import { ContentPage, ContentSection } from "@/components/ContentPage";
import styles from "@/components/ContentPage.module.css";
import { ExternalLink } from "@/components/ExternalLink";
import { PAGES, PAGES_UPDATED } from "@/lib/pages";

export const metadata: Metadata = {
  title: "Flood insurance and Flood Re: PerilMap",
  description:
    "How Flood Re helps many UK households near flood zones get affordable home insurance, who it can help, and what to ask an insurer.",
};

const FLOOD_RE = "https://www.floodre.co.uk/";
const ELIGIBILITY = "https://www.floodre.co.uk/faq_categories/eligibility/";
const BUILD_BACK_BETTER = "https://www.floodre.co.uk/buildbackbetter/";
const NATIONAL_FLOOD_FORUM = "https://www.nationalfloodforum.org.uk/site-pages/flood-re";

export default function FloodInsurancePage() {
  return (
    <ContentPage
      title="Flood insurance and Flood Re"
      lead="Living near a flood zone can make home insurance harder to find or more expensive. Flood Re is a UK scheme that helps many households get affordable cover."
      updated={PAGES_UPDATED}
    >
      <ContentSection id="what-flood-re-is" title="What Flood Re is">
        <p>
          Flood Re is a joint scheme between the government and insurers. It started in April 2016
          and is due to end in 2039, when the aim is for flood insurance to be affordable on the
          open market.
        </p>
        <p>
          You don&apos;t apply to Flood Re yourself. You buy home insurance in the usual way, and if
          your home is at higher risk of flooding, your insurer can pass the flood part of your
          policy to Flood Re. Your insurer still sells the policy and handles any claim.
        </p>
      </ContentSection>

      <ContentSection id="who-it-helps" title="Who it can help">
        <p>Flood Re&apos;s own rules say a policy can qualify when the home:</p>
        <ul>
          <li>was built before 1 January 2009</li>
          <li>has a domestic Council Tax band, or the equivalent</li>
          <li>is used as a private home</li>
          <li>is insured in a person&apos;s name, not a company&apos;s</li>
          <li>is a single home, or a building with up to three homes</li>
          <li>is in England, Wales, Scotland or Northern Ireland</li>
        </ul>
        <p>
          It doesn&apos;t usually cover businesses, or buildings insurance for blocks of more than
          three flats. Tenants and leaseholders in larger blocks can still get contents insurance
          through it. Read the{" "}
          <ExternalLink href={ELIGIBILITY}>
            full eligibility rules on Flood Re&apos;s website
          </ExternalLink>
          .
        </p>
      </ContentSection>

      <ContentSection id="newer-homes" title="Homes built from 2009">
        <p className={styles.note}>
          Homes built on or after 1 January 2009 can&apos;t get help from Flood Re. If you&apos;re
          thinking of buying a newer home near a flood zone, get insurance quotes before you commit.
        </p>
      </ContentSection>

      <ContentSection id="build-back-better" title="Build Back Better">
        <p>
          Some insurers offer up to £10,000 extra after a flood to make repairs more resilient, such
          as raising electrics or fitting flood doors, so the next flood does less damage. It&apos;s
          only available if your policy includes it, so ask before you buy.{" "}
          <ExternalLink href={BUILD_BACK_BETTER}>
            See which insurers offer Build Back Better
          </ExternalLink>
          .
        </p>
      </ContentSection>

      <ContentSection id="what-to-do" title="What you can do">
        <ul>
          <li>
            Ask an insurer or broker whether your policy is supported by Flood Re, and whether it
            includes Build Back Better.
          </li>
          <li>
            Use the <ExternalLink href={FLOOD_RE}>Flood Re website</ExternalLink> to check whether a
            home is likely to qualify and to find insurers that take part.
          </li>
          <li>
            The <ExternalLink href={NATIONAL_FLOOD_FORUM}>National Flood Forum</ExternalLink>, a
            charity, can help you understand your options on 01299 403 055. It can&apos;t give
            advice on a specific policy.
          </li>
        </ul>
        <p>
          Flood Re is changing some of how it works from 2027, so check its website for the latest
          details.
        </p>
      </ContentSection>

      <ContentSection id="perilmap" title="How this relates to PerilMap">
        <p>
          PerilMap shows the Environment Agency&apos;s flood zones around a home. Insurers use their
          own flood models and details about the home itself, so a quote can differ from what
          PerilMap shows. Read more in <Link href={PAGES.about.href}>{PAGES.about.label}</Link>.
        </p>
        <p>
          This page is general information, not insurance advice. PerilMap has no link to Flood Re
          or any insurer, and earns nothing from them.
        </p>
      </ContentSection>
    </ContentPage>
  );
}
