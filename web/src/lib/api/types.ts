/** Friendly names for the API's contract. schema.d.ts is generated, so don't edit that by hand. */

import type { components } from "./schema";

type Schemas = components["schemas"];

export type Assessment = Schemas["AssessmentResponse"];
export type PerilResult = Schemas["PerilResponse"];
export type NearestZones = Schemas["NearestZonesResponse"];
export type AreaComparison = Schemas["AreaComparisonResponse"];
export type Zone = Schemas["ZoneResponse"];
export type DataSource = Schemas["SourceResponse"];
export type GuidanceLink = Schemas["LinkResponse"];
export type PostcodeResult = Schemas["PostcodeResponse"];
export type ZoneMap = Schemas["ZoneMapResponse"];
export type ZoneShape = Schemas["ZoneShapeResponse"];
