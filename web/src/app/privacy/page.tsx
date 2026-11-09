import type { Metadata } from "next";
import Link from "next/link";
import { ContentPage, ContentSection } from "@/components/ContentPage";
import styles from "@/components/ContentPage.module.css";
import { ExternalLink } from "@/components/ExternalLink";
import { PAGES, PAGES_UPDATED, REPO } from "@/lib/pages";

export const metadata: Metadata = {
  title: "Privacy: PerilMap",
  description:
    "PerilMap works without knowing who you are. Searches aren't saved, and there are no accounts, cookies or tracking.",
};

const PROVIDERS = [
  {
    name: "Vercel",
    role: "hosts the website",
    text: "Like any website host, it sees your internet address and which pages you open. It keeps basic records of page requests for about an hour on PerilMap's plan. No page's web address holds a postcode or location.",
    link: "https://vercel.com/legal/privacy-policy",
    linkLabel: "Vercel's privacy policy",
  },
  {
    name: "Google Cloud",
    role: "runs PerilMap's server, in London",
    text: "It passes your request to PerilMap's server. Google's own request records for the server are switched off, so your internet address isn't kept there.",
    link: "https://cloud.google.com/terms/cloud-privacy-notice",
    linkLabel: "Google Cloud's privacy notice",
  },
  {
    name: "postcodes.io",
    role: "finds where a postcode is",
    text: "PerilMap's server asks it on your behalf, so it sees the postcode but not your internet address or anything else about you.",
    link: "https://postcodes.io/",
    linkLabel: "About postcodes.io",
  },
  {
    name: "OpenFreeMap",
    role: "supplies the map images",
    text: "Your browser fetches the map images straight from OpenFreeMap, so it sees your internet address and which part of the map you're looking at, but not the postcode or the pin. Its policy says its normal logs don't include internet addresses and are deleted after 7 days. PerilMap tells your browser not to send the address of the page with these requests.",
    link: "https://openfreemap.org/privacy/",
    linkLabel: "OpenFreeMap's privacy policy",
  },
];

export default function PrivacyPage() {
  return (
    <ContentPage
      title="Privacy"
      lead="PerilMap is built to work without knowing who you are. There are no accounts, cookies, tracking or adverts, and searches aren't saved."
      updated={PAGES_UPDATED}
    >
      <ContentSection id="your-search" title="What happens to your search">
        <p>
          When you search for a postcode or check a spot on the map, your browser sends the postcode
          or the pin&apos;s position to PerilMap&apos;s server. The server uses it to answer, then
          forgets it.
        </p>
        <ul>
          <li>Postcodes and locations aren&apos;t saved, and aren&apos;t written to any log.</li>
          <li>
            They&apos;re sent inside the request, never in a web address, so they can&apos;t end up
            in your browser history, a bookmark or anyone&apos;s logs.
          </li>
          <li>Error messages never repeat them.</li>
          <li>
            Results only exist in your browser tab. Close it and they&apos;re gone. Printing or
            saving a PDF happens on your own device.
          </li>
        </ul>
      </ContentSection>

      <ContentSection id="cookies" title="Cookies and tracking">
        <p>
          PerilMap doesn&apos;t use cookies, analytics, adverts or tracking of any kind, and it
          doesn&apos;t store anything in your browser. That&apos;s why there&apos;s no cookie
          banner.
        </p>
      </ContentSection>

      <ContentSection id="other-services" title="Other services PerilMap uses">
        <p>A few services help run PerilMap. Each one only gets what it needs to do its job.</p>
        <ul className={styles.panel}>
          {PROVIDERS.map((provider) => (
            <li key={provider.name}>
              <h3>
                {provider.name}, which {provider.role}
              </h3>
              <p>{provider.text}</p>
              <p>
                <ExternalLink href={provider.link}>{provider.linkLabel}</ExternalLink>
              </p>
            </li>
          ))}
        </ul>
      </ContentSection>

      <ContentSection id="heavy-use" title="Limiting heavy use">
        <p>
          To stop anyone overloading the service, PerilMap&apos;s server counts how many requests
          come from each internet address in a minute. Addresses are scrambled with a secret key
          that&apos;s never saved, kept only in the server&apos;s memory, and forgotten once the
          minute has passed.
        </p>
      </ContentSection>

      <ContentSection id="links" title="Links to other sites">
        <p>
          Results link to official guidance, such as GOV.UK. Those sites open in a new tab and have
          their own privacy policies.
        </p>
      </ContentSection>

      <ContentSection id="who" title="Who runs PerilMap">
        <p>
          PerilMap is a free, non-commercial project by{" "}
          <ExternalLink href="https://shazmoghaddam.github.io/">Shaz Moghaddam</ExternalLink>, in
          London. Its code is public on <ExternalLink href={REPO}>GitHub</ExternalLink>, so anyone
          can check how it handles data.
        </p>
        <p>
          Because PerilMap doesn&apos;t keep any information about you, there&apos;s nothing to look
          up, correct or delete. If you have a question about your privacy, get in touch through{" "}
          <ExternalLink href="https://shazmoghaddam.github.io/">Shaz&apos;s website</ExternalLink>.
          You can also complain to the{" "}
          <ExternalLink href="https://ico.org.uk/make-a-complaint/">
            Information Commissioner&apos;s Office
          </ExternalLink>
          , the UK&apos;s data protection regulator.
        </p>
        <p>
          To report a security problem, follow the{" "}
          <ExternalLink href={`${REPO}/blob/main/SECURITY.md`}>security policy</ExternalLink>.
        </p>
      </ContentSection>

      <ContentSection id="changes" title="Changes to this page">
        <p>
          The date at the top shows when this page last changed. Every change is recorded in the{" "}
          <ExternalLink href={`${REPO}/blob/main/CHANGELOG.md`}>changelog</ExternalLink>. For how
          the results are worked out, read <Link href={PAGES.about.href}>{PAGES.about.label}</Link>.
        </p>
      </ContentSection>
    </ContentPage>
  );
}
