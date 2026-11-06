"""What the API accepts and returns. This is the contract the frontend relies on."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from perilmap.core.models import (
    AreaComparison,
    Assessment,
    DataSource,
    Link,
    Measurement,
    NearestZones,
    PerilResult,
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AssessmentRequest(Strict):
    latitude: Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False, strict=True)]
    longitude: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False, strict=True)]


class PostcodeRequest(Strict):
    postcode: Annotated[str, Field(min_length=1, max_length=16)]


class PostcodeResponse(Strict):
    postcode: str
    latitude: float
    longitude: float
    attribution: str


class SourceResponse(Strict):
    name: str
    publisher: str
    licence: str
    url: str
    attribution: str
    last_updated: str
    resolution: str


class LinkResponse(Strict):
    label: str
    url: str


class ZoneResponse(Strict):
    band: str
    metres: float | None
    label: str


class NearestZonesResponse(Strict):
    type: Literal["nearest_zones"] = "nearest_zones"
    zones: tuple[ZoneResponse, ...]
    search_radius_metres: float


class AreaComparisonResponse(Strict):
    type: Literal["area_comparison"] = "area_comparison"
    value: float
    unit: str
    group: str
    range_low: float
    range_high: float
    calculation_note: str


class PerilResponse(Strict):
    peril_id: str
    title: str
    status: str
    summary: str
    what_this_means: str
    how_sure: str
    what_you_can_do: tuple[str, ...]
    sources: tuple[SourceResponse, ...]
    measurement: NearestZonesResponse | AreaComparisonResponse | None
    caveats: tuple[str, ...]
    links: tuple[LinkResponse, ...]


class AssessmentResponse(Strict):
    available_here: bool
    region_id: str | None
    region_name: str | None
    message: str | None
    disclaimer: str
    not_covered: tuple[str, ...]
    results: tuple[PerilResponse, ...]


class HealthResponse(Strict):
    status: Literal["ok"] = "ok"


class ErrorResponse(Strict):
    detail: str


def _source(source: DataSource) -> SourceResponse:
    return SourceResponse(
        name=source.name,
        publisher=source.publisher,
        licence=source.licence,
        url=source.url,
        attribution=source.attribution,
        last_updated=source.last_updated,
        resolution=source.resolution,
    )


def _link(link: Link) -> LinkResponse:
    return LinkResponse(label=link.label, url=link.url)


def _measurement(
    measurement: Measurement | None,
) -> NearestZonesResponse | AreaComparisonResponse | None:
    if isinstance(measurement, NearestZones):
        return NearestZonesResponse(
            zones=tuple(
                ZoneResponse(band=zone.band, metres=zone.metres, label=zone.label)
                for zone in measurement.zones
            ),
            search_radius_metres=measurement.search_radius_metres,
        )
    if isinstance(measurement, AreaComparison):
        return AreaComparisonResponse(
            value=measurement.value,
            unit=measurement.unit,
            group=measurement.group,
            range_low=measurement.range_low,
            range_high=measurement.range_high,
            calculation_note=measurement.calculation_note,
        )
    return None


def _result(result: PerilResult) -> PerilResponse:
    return PerilResponse(
        peril_id=result.peril_id,
        title=result.title,
        status=result.status.value,
        summary=result.summary,
        what_this_means=result.what_this_means,
        how_sure=result.how_sure,
        what_you_can_do=result.what_you_can_do,
        sources=tuple(_source(source) for source in result.sources),
        measurement=_measurement(result.measurement),
        caveats=result.caveats,
        links=tuple(_link(link) for link in result.links),
    )


def assessment_response(assessment: Assessment) -> AssessmentResponse:
    return AssessmentResponse(
        available_here=assessment.available_here,
        region_id=assessment.region_id,
        region_name=assessment.region_name,
        message=assessment.message,
        disclaimer=assessment.disclaimer,
        not_covered=assessment.not_covered,
        results=tuple(_result(result) for result in assessment.results),
    )
