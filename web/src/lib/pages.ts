/** The site's own reading pages, in the order they're listed in the header and footer. */
export const PAGES = {
  about: { href: "/about", label: "About the data" },
  floodInsurance: { href: "/flood-insurance", label: "Flood insurance and Flood Re" },
  privacy: { href: "/privacy", label: "Privacy" },
} as const;

/** When the reading pages were last checked against their sources. */
export const PAGES_UPDATED = "9 November 2026";

export const REPO = "https://github.com/Moghaddam-Labs/perilmap";
