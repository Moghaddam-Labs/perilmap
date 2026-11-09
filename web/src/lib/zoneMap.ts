/**
 * Flood zones drawn on the map. The shapes come from the same grid squares the result cards measure,
 * so the map and the distances in words always agree.
 */

import { bandDisplay, type BandPattern } from "@/lib/bands";
import type { Position } from "@/lib/geo";
import type { ZoneMap } from "@/lib/api/types";

export interface MapLayerChoice {
  perilId: string;
  label: string;
}

/** The checks that can be drawn, in the order they're offered. Rivers and sea is shown first. */
export const FLOOD_MAP_LAYERS: readonly MapLayerChoice[] = [
  { perilId: "flood_rivers_and_sea", label: "Rivers and sea" },
  { perilId: "flood_surface_water", label: "Surface water" },
];

/** Areas with no data use the neutral pattern, which never stands for a flood level. */
export const NO_DATA = "No data";

/** Lowest band first, so higher bands are drawn on top. */
const DRAW_ORDER = ["Very Low", "Low", "Medium", "High"];

type MultiPolygon = ZoneMap["no_data_areas"];

interface ZoneProperties {
  band: string;
  pattern: BandPattern;
}

type ZoneFeature = GeoJSON.Feature<GeoJSON.MultiPolygon, ZoneProperties>;

function feature(coordinates: MultiPolygon, properties: ZoneProperties): ZoneFeature {
  return {
    type: "Feature",
    properties,
    geometry: { type: "MultiPolygon", coordinates: coordinates as GeoJSON.Position[][][] },
  };
}

function drawRank(band: string) {
  const rank = DRAW_ORDER.indexOf(band);
  return rank === -1 ? DRAW_ORDER.length : rank;
}

/** The zones as map features, lowest band first, with areas that have no data on top. */
export function zoneFeatures(
  zoneMap: ZoneMap | null,
): GeoJSON.FeatureCollection<GeoJSON.MultiPolygon, ZoneProperties> {
  if (!zoneMap) return { type: "FeatureCollection", features: [] };
  const shapes = [...zoneMap.shapes].sort((a, b) => drawRank(a.band) - drawRank(b.band));
  const features = shapes.map((shape) =>
    feature(shape.coordinates, { band: shape.band, pattern: bandDisplay(shape.band).pattern }),
  );
  if (zoneMap.no_data_areas.length) {
    features.push(feature(zoneMap.no_data_areas, { band: NO_DATA, pattern: "other" }));
  }
  return { type: "FeatureCollection", features };
}

const EARTH_RADIUS_METRES = 6_371_008.8;

/** A circle on the map, as a polygon with enough sides to look round. */
export function searchCircle(
  centre: Position,
  radiusMetres: number,
  sides = 96,
): GeoJSON.Feature<GeoJSON.Polygon> {
  const latitude = (centre.latitude * Math.PI) / 180;
  const longitude = (centre.longitude * Math.PI) / 180;
  const angle = radiusMetres / EARTH_RADIUS_METRES;
  const ring: GeoJSON.Position[] = [];
  for (let step = 0; step <= sides; step += 1) {
    const bearing = ((step % sides) / sides) * 2 * Math.PI;
    const pointLatitude = Math.asin(
      Math.sin(latitude) * Math.cos(angle) +
        Math.cos(latitude) * Math.sin(angle) * Math.cos(bearing),
    );
    const pointLongitude =
      longitude +
      Math.atan2(
        Math.sin(bearing) * Math.sin(angle) * Math.cos(latitude),
        Math.cos(angle) - Math.sin(latitude) * Math.sin(pointLatitude),
      );
    ring.push([(pointLongitude * 180) / Math.PI, (pointLatitude * 180) / Math.PI]);
  }
  return { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [ring] } };
}

/** The south-west and north-east corners of a circle, for fitting the map to it. */
export function circleBounds(circle: GeoJSON.Feature<GeoJSON.Polygon>) {
  const ring = circle.geometry.coordinates[0] ?? [];
  const longitudes = ring.map((point) => point[0] as number);
  const latitudes = ring.map((point) => point[1] as number);
  return [
    [Math.min(...longitudes), Math.min(...latitudes)],
    [Math.max(...longitudes), Math.max(...latitudes)],
  ] as [[number, number], [number, number]];
}

/** The bands to show in the key, highest first, plus whether any area has no data. */
export function shownBands(zoneMap: ZoneMap | null) {
  if (!zoneMap) return { bands: [], noData: false };
  const bands = zoneMap.shapes.map((shape) => shape.band).sort((a, b) => drawRank(b) - drawRank(a));
  return { bands, noData: zoneMap.no_data_areas.length > 0 };
}
