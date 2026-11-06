/** Matches the API's own check, so obvious mistakes are caught without sending anything. */
const POSTCODE_PATTERN = /^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$/;

/** Returns the postcode tidied up, such as "SW1A 2AA", or null if it isn't shaped like one. */
export function normalisePostcode(text: string): string | null {
  const cleaned = text.toUpperCase().split(/\s+/).filter(Boolean).join(" ");
  if (!POSTCODE_PATTERN.test(cleaned)) {
    return null;
  }
  const compact = cleaned.replace(" ", "");
  return `${compact.slice(0, -3)} ${compact.slice(-3)}`;
}
