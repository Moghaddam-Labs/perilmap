#!/usr/bin/env bash
# Build and deploy the API to Cloud Run with its cost and privacy settings.
# The "^|^" below uses | to separate settings, because a website list contains commas.
# Usage: scripts/deploy.sh [allowed website, such as https://perilmap.example]
set -euo pipefail

PROJECT="perilmap"
REGION="europe-west2"
SERVICE="perilmap-api"
ALLOWED_ORIGINS="${1:-}"

for file in rivers_and_sea_5m.tif surface_water_5m.tif heat_air_temperature.gpkg heat_air_temperature.json; do
  if [[ ! -f "grids/${file}" ]]; then
    echo "Missing grids/${file}. Add the built data files first." >&2
    exit 1
  fi
done

gcloud run deploy "${SERVICE}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --source . \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --concurrency 10 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 30 \
  --cpu-throttling \
  --set-env-vars "^|^PERILMAP_TRUST_FORWARDED_FOR=true|PERILMAP_ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"
