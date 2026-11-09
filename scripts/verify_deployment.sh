#!/usr/bin/env bash
# Check a running API behaves as intended.
# Usage: scripts/verify_deployment.sh https://your-service-url
set -uo pipefail

URL="${1:?Give the service URL}"
JSON="Content-Type: application/json"
failures=0

check() {
  if [[ "$2" == "$3" ]]; then
    echo "OK    $1"
  else
    echo "FAIL  $1 (expected $3, got $2)"
    failures=$((failures + 1))
  fi
}

contains() {
  if [[ "$2" == *"$3"* ]]; then
    echo "OK    $1"
  else
    echo "FAIL  $1 (missing: $3)"
    failures=$((failures + 1))
  fi
}

post() {
  curl -s -m 60 -X POST "${URL}$1" -H "${JSON}" -d "$2" "${@:3}"
}

status() {
  curl -s -m 60 -o /dev/null -w '%{http_code}' "$@"
}

check "Health check" "$(status "${URL}/health")" "200"
check "Docs are off" "$(status "${URL}/docs")" "404"
check "Location in the address is refused" \
  "$(status "${URL}/v1/assessments?latitude=51.5&longitude=-0.1")" "405"

stratford="$(post /v1/assessments '{"latitude": 51.543, "longitude": -0.002}')"
contains "Stratford has a rivers and sea result" "${stratford}" '"flood_rivers_and_sea"'
contains "Stratford has a surface water result" "${stratford}" '"flood_surface_water"'
contains "Stratford has a heat result" "${stratford}" '"heat"'
contains "Stratford has the subsidence card" "${stratford}" '"subsidence"'
if [[ "${stratford}" == *"temporarily_unavailable"* ]]; then
  check "No check failed" "failed" "none failed"
fi

brighton="$(post /v1/assessments '{"latitude": 50.8225, "longitude": -0.1372}')"
contains "Brighton is not available yet" "${brighton}" "Not available here yet"

postcode="$(post /v1/postcodes/lookup '{"postcode": "SW1A 2AA"}')"
contains "Live postcode lookup works" "${postcode}" '"latitude"'

invalid="$(post /v1/assessments '{"latitude": 95.654321, "longitude": 0}')"
if [[ "${invalid}" == *"95.654"* ]]; then
  check "Errors don't repeat the location" "repeated" "not repeated"
else
  echo "OK    Errors don't repeat the location"
fi

headers="$(curl -s -m 60 -D - -o /dev/null "${URL}/health" | tr '[:upper:]' '[:lower:]')"
contains "Replies aren't cached" "${headers}" "cache-control: no-store"
contains "Security policy is set" "${headers}" "content-security-policy"

# Change the part of the header a visitor controls. The limit should still apply.
limited=""
for attempt in $(seq 1 40); do
  code="$(status -X POST "${URL}/v1/assessments" -H "${JSON}" \
    -H "X-Forwarded-For: 203.0.113.${attempt}" \
    -d '{"latitude": 51.5, "longitude": -0.1}')"
  if [[ "${code}" == "429" ]]; then
    limited="yes"
    break
  fi
done
check "Faking an address can't dodge the rate limit" "${limited:-no}" "yes"

echo
if ((failures > 0)); then
  echo "${failures} check(s) failed."
  exit 1
fi
echo "All checks passed."
echo
# The rate limit check above uses up this computer's allowance for a minute.
echo "Wait a minute before testing the website from this computer, or searches will be refused."
