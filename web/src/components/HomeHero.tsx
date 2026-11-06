import { BrandMark } from "./BrandMark";
import styles from "./HomeHero.module.css";

/** The opening of the home page, matching the repo's banner: the Thames, a pin and its search circle. */
export function HomeHero() {
  return (
    <header className={styles.hero}>
      <div className={styles.map} aria-hidden="true">
        {/* next/image adds an inline style, which the site's content security policy blocks. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/brand/thames-flood-zones.webp"
          alt=""
          width={1400}
          height={700}
          fetchPriority="high"
        />
        <svg viewBox="0 0 1400 700" className={styles.pin} focusable="false">
          <circle className={styles.circle} cx="931" cy="420" r="112.3" />
          <line className={styles.line} x1="931" y1="420" x2="884" y2="522" />
          <circle className={styles.white} cx="884" cy="522" r="6" />
          <circle className={styles.white} cx="931" cy="420" r="15" />
          <circle className={styles.hole} cx="931" cy="420" r="6" />
        </svg>
      </div>
      <div className={styles.inner}>
        <p className={styles.wordmark}>
          <BrandMark />
          PerilMap
        </p>
        <h1 className={styles.title}>
          See the climate risks around a home, before the insurance quote arrives.
        </h1>
        <p className={styles.lead}>
          PerilMap looks at flooding, summer heat and ground movement around a spot in London. For
          each one, it says what the result means, how sure it is and what you can do next.
        </p>
      </div>
    </header>
  );
}
