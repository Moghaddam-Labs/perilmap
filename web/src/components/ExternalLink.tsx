import type { ReactNode } from "react";
import { safeExternalUrl } from "@/lib/urls";

/**
 * A link to another site. The address may come from the API, so anything other than a normal web
 * address is shown as plain text instead of a link.
 */
export function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  const safe = safeExternalUrl(href);
  if (!safe) {
    return <>{children}</>;
  }
  return (
    <a href={safe} target="_blank" rel="noopener noreferrer">
      {children}
      <span className="visually-hidden">, opens in a new tab</span>
    </a>
  );
}
