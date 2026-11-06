/** Settings the website reads from the environment, checked so a typo can't weaken security. */

export const LIVE_API_URL = "https://perilmap-api-762501502533.europe-west2.run.app";

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1"]);

/** Returns the API's origin. Only local development may use plain http. */
export function apiOrigin(value: string | undefined = process.env.NEXT_PUBLIC_PERILMAP_API_URL) {
  const raw = value?.trim() || LIVE_API_URL;
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new Error("NEXT_PUBLIC_PERILMAP_API_URL isn't a valid web address.");
  }
  const allowed =
    url.protocol === "https:" || (url.protocol === "http:" && LOCAL_HOSTS.has(url.hostname));
  if (!allowed) {
    throw new Error("NEXT_PUBLIC_PERILMAP_API_URL must use https, except on this computer.");
  }
  return url.origin;
}

/** The design system page is for development and review, so it's hidden on the live site. */
export function isDesignPageEnabled(
  environment: Partial<Record<"NODE_ENV" | "PERILMAP_SHOW_DESIGN_PAGE", string>> = process.env,
) {
  return environment.NODE_ENV === "development" || environment.PERILMAP_SHOW_DESIGN_PAGE === "true";
}
