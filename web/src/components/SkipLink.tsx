import styles from "./SkipLink.module.css";

export function SkipLink() {
  return (
    <a className={styles.skip} href="#main">
      Skip to main content
    </a>
  );
}
