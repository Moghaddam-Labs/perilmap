import styles from "./BrandMark.module.css";

/** The search circle around a pin: PerilMap's mark, and how it measures nearby zones. */
export function BrandMark() {
  return (
    <svg className={styles.mark} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <circle className={styles.ring} cx="16" cy="16" r="14" />
      <circle className={styles.pin} cx="16" cy="16" r="6" />
      <circle className={styles.hole} cx="16" cy="16" r="2.4" />
    </svg>
  );
}
