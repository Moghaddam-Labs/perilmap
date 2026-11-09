import type { ReactNode } from "react";
import styles from "./ContentPage.module.css";

interface ContentPageProps {
  title: string;
  lead: ReactNode;
  /** When the page was last checked, written out, such as "9 November 2026". */
  updated: string;
  children: ReactNode;
}

/** A page of reading, such as the privacy notice, with a comfortable line length. */
export function ContentPage({ title, lead, updated, children }: ContentPageProps) {
  return (
    <main id="main" className={styles.page}>
      <header className={styles.header}>
        <h1>{title}</h1>
        <p className={styles.lead}>{lead}</p>
        <p className={styles.updated}>Last updated {updated}</p>
      </header>
      <div className={styles.body}>{children}</div>
    </main>
  );
}

/** A titled part of a content page, so headings and spacing stay the same on every page. */
export function ContentSection({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section aria-labelledby={id} className={styles.section}>
      <h2 id={id}>{title}</h2>
      {children}
    </section>
  );
}
