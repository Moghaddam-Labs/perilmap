/** The browser rules that limit what any page on this site can load or send. */

import { MAP_TILE_ORIGIN } from "./map";

export interface ContentSecurityPolicyOptions {
  nonce: string;
  apiOrigin: string;
  development?: boolean;
}

export function contentSecurityPolicy({
  nonce,
  apiOrigin,
  development = false,
}: ContentSecurityPolicyOptions) {
  // A nonce would switch off 'unsafe-inline', and the dev server's live reload needs it.
  const developmentOnly = development
    ? { script: ["'unsafe-eval'"], style: ["'unsafe-inline'"], connect: ["ws:"] }
    : { script: [], style: [], connect: [] };

  const directives: Record<string, string[]> = {
    "default-src": ["'self'"],
    "script-src": ["'self'", `'nonce-${nonce}'`, "'strict-dynamic'", ...developmentOnly.script],
    "style-src": ["'self'", ...developmentOnly.style],
    // The map draws its images from data it has already downloaded.
    "img-src": ["'self'", "data:", "blob:"],
    "font-src": ["'self'"],
    // Locations may only be sent to the site itself and PerilMap's API. The map images come from
    // OpenFreeMap, which sees which area of the map is shown, but not the postcode or the pin.
    "connect-src": ["'self'", apiOrigin, MAP_TILE_ORIGIN, ...developmentOnly.connect],
    // The map's worker file is served by the site itself. 'strict-dynamic' would otherwise block it.
    "worker-src": ["'self'"],
    "object-src": ["'none'"],
    "base-uri": ["'none'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
  };
  if (!development) {
    directives["upgrade-insecure-requests"] = [];
  }
  return Object.entries(directives)
    .map(([name, values]) => [name, ...values].join(" "))
    .join("; ");
}

export const staticSecurityHeaders = [
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  // A results page must never tell another site which home someone was looking at.
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];
