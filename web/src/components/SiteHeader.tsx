import Link from "next/link";
import { BrandMark } from "./BrandMark";
import styles from "./SiteHeader.module.css";

export function SiteHeader() {
  return (
    <header className={styles.bar}>
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
            <Link href="/#privacy">Privacy</Link>
          </li>
        </ul>
      </nav>
    </header>
  );
}
