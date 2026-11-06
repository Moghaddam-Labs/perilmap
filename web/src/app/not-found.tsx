import type { Metadata } from "next";
import Link from "next/link";
import styles from "./not-found.module.css";

export const metadata: Metadata = { title: "Page not found: PerilMap" };

export default function NotFound() {
  return (
    <main id="main" className={styles.main}>
      <h1>Page not found</h1>
      <p>
        Check the web address, or <Link href="/">go to the PerilMap home page</Link>.
      </p>
    </main>
  );
}
