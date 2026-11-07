/**
 * Every dataset the site uses. The dates and details match the API's own wording, and a test in
 * tests/api/test_contract.py fails if they drift apart.
 */

export interface DataSourceSummary {
  label: string;
  publisher: string;
  href: string;
  updated: string;
  detail: string;
}

const EA_UPDATED = "6 July 2026, downloaded November 2026";
const FLOOD_DETAIL = "5 m grid built from the Environment Agency's mapping, mostly on a 2 m grid";

export const DATA_SOURCES: DataSourceSummary[] = [
  {
    label: "Rivers and sea flood zones",
    publisher: "Environment Agency",
    href: "https://www.data.gov.uk/dataset/943d2bbb-aa08-45d1-96cb-42556cd01d94/risk-of-flooding-from-rivers-and-sea2",
    updated: EA_UPDATED,
    detail: FLOOD_DETAIL,
  },
  {
    label: "Surface water flood zones",
    publisher: "Environment Agency",
    href: "https://www.data.gov.uk/dataset/risk-of-flooding-from-surface-water3",
    updated: EA_UPDATED,
    detail: FLOOD_DETAIL,
  },
  {
    label: "Summer air temperature",
    publisher: "Greater London Authority, Bloomberg Associates and Arup",
    href: "https://data.london.gov.uk/dataset/climate-risk-mapping",
    updated: "September 2024, covering summers from 2018 to 2022",
    detail: "Neighbourhood areas (LSOAs), typically about 0.2 km²",
  },
  {
    label: "Ground movement",
    publisher: "British Geological Survey",
    href: "https://www.bgs.ac.uk/datasets/bgs-geosure-5-km-hex-grid/",
    updated: "Version 8, in a data file dated November 2019",
    detail: "National summary, with hexagons of about 65 km²",
  },
  {
    label: "Postcode lookup",
    publisher: "postcodes.io",
    href: "https://postcodes.io/",
    updated: "Looked up each time you search",
    detail: "PerilMap's server asks for the postcode, so postcodes.io doesn't see who's searching",
  },
];
