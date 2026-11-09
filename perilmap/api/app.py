"""The web API. Locations and postcodes only ever arrive in request bodies, and are never kept."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from perilmap.api import postcodes
from perilmap.api.rate_limit import RateLimiter
from perilmap.api.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    ErrorResponse,
    HealthResponse,
    PostcodeRequest,
    PostcodeResponse,
    ZoneMapRequest,
    ZoneMapResponse,
    assessment_response,
    zone_map_response,
)
from perilmap.api.settings import Settings
from perilmap.core.assessment import RegionRegistry, assess, zone_map
from perilmap.core.models import Location

logger = logging.getLogger(__name__)

MAX_BODY_BYTES = 1_024
INVALID_REQUEST = "That request isn't valid. Check it and try again."
SERVER_ERROR = "Something went wrong on our side. Try again shortly."
NO_ZONE_MAP = "There's nothing to draw on the map for this check here."
RATE_LIMITED = "Too many requests. Wait a moment and try again."
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}


def client_address(request: Request, trust_forwarded_for: bool) -> str:
    """Identify a visitor for rate limiting, without letting them choose their own identity."""
    if trust_forwarded_for:
        # Visitors can add entries to this header, but only the proxy can add the last one.
        forwarded = request.headers.get("x-forwarded-for", "")
        last = forwarded.rsplit(",", 1)[-1].strip()
        if last:
            return last
    return request.client.host if request.client else "unknown"


def create_app(
    registry: RegionRegistry | Callable[[], RegionRegistry],
    settings: Settings | None = None,
    postcode_client: postcodes.PostcodeClient | None = None,
) -> FastAPI:
    """Build the app. The regions are passed in, so the API stays free of region details."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Load the data before taking requests, so a missing file stops the app from starting.
        app.state.registry = registry() if callable(registry) else registry
        app.state.postcodes = postcode_client or postcodes.PostcodeClient(
            settings.postcode_timeout_seconds
        )
        yield
        app.state.postcodes.close()

    app = FastAPI(
        title="PerilMap API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.show_docs else None,
    )
    limiter = RateLimiter(settings.client_requests_per_minute, settings.total_requests_per_minute)
    app.state.rate_limiter = limiter

    @app.middleware("http")
    async def protect(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Apply the size limit and rate limit, and add the security headers to every reply."""
        response = _refuse_early(request)
        if response is None:
            try:
                response = await call_next(request)
            except Exception as error:
                # Only the error's type is logged, because its details could hold a location.
                logger.error("Request failed with %s", type(error).__name__)
                response = JSONResponse({"detail": SERVER_ERROR}, status_code=500)
        for name, value in SECURITY_HEADERS.items():
            # The optional docs page needs to load scripts, which this policy would block.
            if name == "Content-Security-Policy" and request.url.path == "/docs":
                continue
            response.headers[name] = value
        return response

    def _refuse_early(request: Request) -> Response | None:
        if request.method != "POST":
            return None
        length = request.headers.get("content-length", "")
        if not length.isdigit() or int(length) > MAX_BODY_BYTES:
            return JSONResponse({"detail": INVALID_REQUEST}, status_code=413)
        decision = limiter.check(client_address(request, settings.trust_forwarded_for))
        if not decision.allowed:
            return JSONResponse(
                {"detail": RATE_LIMITED},
                status_code=429,
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )
        return None

    # Added after the middleware above, so browsers still see its replies as allowed.
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_methods=["POST"],
            allow_headers=["Content-Type"],
            max_age=600,
        )

    # Flood zone shapes make results large, and they shrink to about a sixth when compressed.
    # Added last, so it wraps everything else and compresses every reply.
    # Level 5 is several times quicker than the default 9, for almost the same size.
    app.add_middleware(GZipMiddleware, minimum_size=1_024, compresslevel=5)

    # Zone maps are large, and shrink to about a sixth when compressed. Added last, so it wraps
    # everything else. Level 5 is much quicker than the default 9, for almost the same size.
    app.add_middleware(GZipMiddleware, compresslevel=5)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
        # FastAPI's default reply repeats the input, which could be someone's location.
        return JSONResponse({"detail": INVALID_REQUEST}, status_code=422)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    errors = {
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    }

    @app.post("/v1/assessments", response_model=AssessmentResponse, responses=errors)
    def create_assessment(body: AssessmentRequest, request: Request) -> AssessmentResponse:
        location = Location(body.latitude, body.longitude)
        return assessment_response(assess(location, request.app.state.registry))

    @app.post(
        "/v1/zone-maps",
        response_model=ZoneMapResponse,
        responses={**errors, 404: {"model": ErrorResponse}},
    )
    def create_zone_map(body: ZoneMapRequest, request: Request) -> ZoneMapResponse:
        location = Location(body.latitude, body.longitude)
        found = zone_map(location, body.peril_id, request.app.state.registry)
        if found is None:
            raise HTTPException(404, NO_ZONE_MAP)
        return zone_map_response(body.peril_id, found)

    @app.post(
        "/v1/postcodes/lookup",
        response_model=PostcodeResponse,
        responses={
            **errors,
            404: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def lookup_postcode(body: PostcodeRequest, request: Request) -> PostcodeResponse:
        try:
            position = request.app.state.postcodes.lookup(body.postcode)
        except postcodes.InvalidPostcode as error:
            raise HTTPException(422, str(error)) from None
        except postcodes.PostcodeNotFound as error:
            raise HTTPException(404, str(error)) from None
        except postcodes.PostcodeServiceError:
            logger.error("The postcode service failed")
            raise HTTPException(503, "Postcode search isn't working right now.") from None
        return PostcodeResponse(
            postcode=position.postcode,
            latitude=position.latitude,
            longitude=position.longitude,
            attribution=postcodes.ATTRIBUTION,
        )

    return app
