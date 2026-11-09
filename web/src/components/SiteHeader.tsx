import Link from "next/link";
import { PAGES } from "@/lib/pages";
import { BrandMark } from "./BrandMark";
import styles from "./SiteHeader.module.css";

export function SiteHeader() {
  return (
    <header className={`${styles.bar} no-print`}>
      <Link href="/" className={styles.wordmark}>
        <BrandMark />
        PerilMap
      </Link>
      <nav aria-label="Main">
        <ul className={styles.links}>
          <li>
            <Link href="/#how-it-works">How it works</Link>
          </li>
          <li>
            <Link href={PAGES.about.href}>{PAGES.about.label}</Link>
          </li>
          <li>
            <Link href={PAGES.privacy.href}>{PAGES.privacy.label}</Link>
          </li>
        </ul>
      </nav>
    </header>
  );
}
