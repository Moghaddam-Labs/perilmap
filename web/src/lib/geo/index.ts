import londonBoundary from "./london-boundary.json";

export interface Position {
  latitude: number;
  longitude: number;
}

const EARTH_RADIUS_METRES = 6_371_008.8;
const COMPASS = [
  "north",
  "north-east",
  "east",
  "south-east",
  "south",
  "south-west",
  "west",
  "north-west",
];

const radians = (degrees: number) => (degrees * Math.PI) / 180;

/** The distance between two places along the ground, in metres. */
export function distanceMetres(from: Position, to: Position) {
  const dLat = radians(to.latitude - from.latitude);
  const dLon = radians(to.longitude - from.longitude);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(radians(from.latitude)) * Math.cos(radians(to.latitude)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_METRES * Math.asin(Math.min(1, Math.sqrt(a)));
}

/** Which way "to" lies from "from", as one of eight compass directions. */
export function compassDirection(from: Position, to: Position) {
  const lat1 = radians(from.latitude);
  const lat2 = radians(to.latitude);
  const dLon = radians(to.longitude - from.longitude);
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  const bearing = (Math.atan2(y, x) * 180) / Math.PI;
  return COMPASS[Math.round(((bearing + 360) % 360) / 45) % 8] as string;
}

function roughDistance(metres: number) {
  if (metres < 1000) {
    return `${Math.max(10, Math.round(metres / 10) * 10)} m`;
  }
  return `${(metres / 1000).toFixed(1)} km`;
}

/** Where the pin is, in words, for people who can't see the map. */
export function describePin(pin: Position, postcodeCentre: Position) {
  const metres = distanceMetres(postcodeCentre, pin);
  if (metres < 5) {
    return "The pin is at the postcode's centre.";
  }
  return `The pin is about ${roughDistance(metres)} ${compassDirection(postcodeCentre, pin)} of the postcode's centre.`;
}

type Ring = number[][];

function insideRing(longitude: number, latitude: number, ring: Ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi = 0, yi = 0] = ring[i] ?? [];
    const [xj = 0, yj = 0] = ring[j] ?? [];
    if (
      yi > latitude !== yj > latitude &&
      longitude < ((xj - xi) * (latitude - yi)) / (yj - yi) + xi
    ) {
      inside = !inside;
    }
  }
  return inside;
}

/**
 * An early warning only, from a simplified boundary. The API makes the real decision, so a spot
 * right on the line may be answered differently.
 */
export function isInsideLondon({ latitude, longitude }: Position) {
  const [outer, ...holes] = londonBoundary.coordinates as Ring[];
  return (
    outer !== undefined &&
    insideRing(longitude, latitude, outer) &&
    !holes.some((hole) => insideRing(longitude, latitude, hole))
  );
}

export const LONDON_BOUNDARY = londonBoundary as { type: "Polygon"; coordinates: Ring[] };
