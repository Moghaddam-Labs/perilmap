"""What London's results say, and where each fact comes from. Kept together for easy review."""

from __future__ import annotations

from perilmap.core.models import DataSource, Link

OGL_V3 = "Open Government Licence v3.0"
EA_ATTRIBUTION = "© Environment Agency copyright and/or database right 2025. All rights reserved."
EA_LAST_UPDATED = "6 July 2026, downloaded November 2026"
FLOOD_RESOLUTION = "5 m grid built from the Environment Agency's mapping, mostly on a 2 m grid"

RIVERS_AND_SEA_SOURCE = DataSource(
    name="Risk of Flooding from Rivers and Sea",
    publisher="Environment Agency",
    licence=OGL_V3,
    url="https://www.data.gov.uk/dataset/943d2bbb-aa08-45d1-96cb-42556cd01d94/risk-of-flooding-from-rivers-and-sea2",
    attribution=EA_ATTRIBUTION,
    last_updated=EA_LAST_UPDATED,
    resolution=FLOOD_RESOLUTION,
)
SURFACE_WATER_SOURCE = DataSource(
    name="Risk of Flooding from Surface Water",
    publisher="Environment Agency",
    licence=OGL_V3,
    url="https://www.data.gov.uk/dataset/risk-of-flooding-from-surface-water3",
    attribution=EA_ATTRIBUTION,
    last_updated=EA_LAST_UPDATED,
    resolution=FLOOD_RESOLUTION,
)
HEAT_SOURCE = DataSource(
    name="Climate Risk Mapping, mean air temperature",
    publisher="Greater London Authority, Bloomberg Associates and Arup",
    licence=OGL_V3,
    url="https://data.london.gov.uk/dataset/climate-risk-mapping",
    attribution="Greater London Authority, using Arup's UHeat model",
    last_updated="September 2024, covering summers from 2018 to 2022",
    resolution="Neighbourhood areas (LSOAs), typically about 0.2 km²",
)
SUBSIDENCE_SOURCE = DataSource(
    name="BGS GeoSure 5 km hex grid, shrink-swell",
    publisher="British Geological Survey",
    licence="Open Government Licence",
    url="https://www.bgs.ac.uk/datasets/bgs-geosure-5-km-hex-grid/",
    attribution="BGS © UKRI. Contains OS data © Crown copyright 2020.",
    last_updated="Version 8, in a data file dated November 2019",
    resolution="National summary, with hexagons of about 65 km²",
)

CHECK_FLOOD_RISK = Link(
    "Check your long term flood risk on GOV.UK", "https://www.gov.uk/check-long-term-flood-risk"
)
FLOOD_WARNINGS = Link("Sign up for flood warnings", "https://www.gov.uk/sign-up-for-flood-warnings")
PREPARE_FOR_FLOODING = Link("Prepare for flooding", "https://www.gov.uk/prepare-for-flooding")
BEAT_THE_HEAT = Link(
    "Beat the heat: keep cool at home checklist",
    "https://www.gov.uk/government/publications/beat-the-heat-hot-weather-advice/beat-the-heat-keep-cool-at-home-checklist",
)
BGS_SHRINK_SWELL = Link(
    "Swelling and shrinking soils, from the British Geological Survey",
    "https://www.bgs.ac.uk/geology-projects/shallow-geohazards/clay-shrink-swell/",
)
BGS_REPORT = Link(
    "Natural subsidence GeoReport from the British Geological Survey (paid)",
    "https://shop.bgs.ac.uk/Shop/Product/GRS_S004",
)

FLOOD_HOW_SURE = (
    "The Environment Agency says this data estimates risk to an area of land and is generally "
    "not suitable for assessing one property. Our distances can read up to about 6 m too close, "
    "and on a zone means on it or within about 5 m."
)
FLOOD_ACTIONS = (
    "Check the official Environment Agency map for this address.",
    "Sign up for free flood warnings if you're near a zone.",
    "Ask your insurer or a surveyor about this particular home before making a decision.",
)
FLOOD_LINKS = (CHECK_FLOOD_RISK, FLOOD_WARNINGS, PREPARE_FOR_FLOODING)

RIVERS_MEANING = (
    "These zones show the chance of flooding from rivers or the sea in any one year, allowing "
    "for flood defences, which reduce the risk but don't remove it. High is 1 in 30 or more, "
    "Medium is between 1 in 30 and 1 in 100, Low is between 1 in 100 and 1 in 1,000, and Very "
    "Low is below 1 in 1,000. Being near a zone doesn't mean this home would flood."
)
SURFACE_MEANING = (
    "These zones show where rainwater may lie or flow when it can't drain away, and the chance "
    "of that in any one year. High is 1 in 30 or more, Medium is between 1 in 30 and 1 in 100, "
    "and Low is between 1 in 100 and 1 in 1,000. The Environment Agency treats anywhere outside "
    "these zones as Very Low, not as no risk. Being near a zone doesn't mean this home would "
    "flood."
)
INCOMPLETE_CAVEAT = (
    "This spot is close to the edge of London or to an area where we don't have data, so a "
    "nearby zone may not be shown."
)
NO_SURFACE_DATA_SUMMARY = "We don't have surface water data for this spot."
NO_SURFACE_DATA_MEANING = (
    "This says nothing about the risk here, either way. It doesn't mean the risk is low."
)
NO_DATA_HOW_SURE = "No result was produced for this spot."

HEAT_DESCRIPTION = "Modelled average air temperature, June to August, day and night, 2018 to 2022"
HEAT_EXPLANATION = (
    "Temperatures across London only vary by about two degrees, so we show how this area "
    "compares, not a risk rating. This is the average outdoor summer temperature, not how hot "
    "your home gets inside or during a heatwave."
)
HEAT_HOW_SURE = (
    "This comes from a computer model, and its authors describe the results as indicative. It "
    "gives one figure for the whole neighbourhood, and differences between areas are small."
)
HEAT_CALCULATION_NOTE = (
    "London's range and the fifths are PerilMap's own calculation from this data."
)
HEAT_ACTIONS = (
    "Use the UK Health Security Agency's checklist to keep your home cool in hot weather.",
    "If you're viewing a home, ask how it copes in summer, including ventilation and shade.",
)
HEAT_LINKS = (BEAT_THE_HEAT,)
NO_HEAT_DATA_SUMMARY = "We don't have a temperature figure for this spot."
NO_HEAT_DATA_MEANING = (
    "This data doesn't cover the River Thames and a few small areas. This says nothing about how "
    "warm it gets here."
)

SUBSIDENCE_SUMMARY = (
    "Much of London sits on clay that can shrink and swell. We can't assess this particular home."
)
SUBSIDENCE_MEANING = (
    "Clay soils shrink as they dry and swell as they get wet, and this movement can damage "
    "foundations and walls. In the British Geological Survey's national summary, about 86% of "
    "London's area falls in its Significant class. That figure is PerilMap's own calculation "
    "from this data."
)
SUBSIDENCE_HOW_SURE = (
    "This is general information for London, not a result for this location. The British "
    "Geological Survey marks this data as not suitable for local or site specific analysis."
)
SUBSIDENCE_ACTIONS = (
    "If you're buying, ask your surveyor about ground conditions and any signs of movement.",
    "Consider a detailed report for this address from the British Geological Survey.",
    "If you notice new or growing cracks, speak to a surveyor or your insurer.",
)
SUBSIDENCE_LINKS = (BGS_SHRINK_SWELL, BGS_REPORT)

NOT_COVERED = (
    "Groundwater flooding",
    "Reservoir flooding",
    "Flooding from sewers and blocked drains",
)
