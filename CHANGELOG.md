# Changelog

All notable changes to PerilMap are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Website styling: pill-shaped controls, softly rounded panels, and a labelled two-tone footer holding
  data credits, licences, project links and the privacy summary.

### Added

- Website foundation in `web/`: Next.js, a design system with accessible flood level patterns and
  status labels, light and dark themes, strict security headers, API types generated from the API's
  contract, and tests for accessibility and colour contrast.
- Deployment setup for Google Cloud Run: a Dockerfile, production-only dependencies, deploy and check
  scripts, a guide, and a CI check that the image builds.
- Web API for assessments and postcode lookups, with rate limiting, security headers and protections
  that keep locations out of logs, web addresses and error replies.
- London plug-in, with flood distances, the heat comparison and the subsidence explainer, each with
  plain-English wording, guidance links and credited sources.
- Backend core and plug-in setup, with rules that make every result explain itself, credit its
  sources and keep gaps in the data from looking safe.
- Heat data: a small file of modelled average summer air temperature for London's neighbourhoods,
  with the source's social measures left out, and labelled comparisons.
- README banner, with its map drawn from Environment Agency flood data for the Thames.
- Repo foundations: README, licence, security policy, contribution notes, CI and Dependabot.
- Flood data test: estimates London's Environment Agency flood data, loads it into PostGIS with a
  size guard, and reports database size, lookup speed and results for 20 known places.

### Added

- Official Greater London boundary, with a check of surface water coverage against it.
- A list of blank surface water squares that show No data, so a gap can never look safe.
- Results outside London show Not available here yet, and results near a gap are marked may be
  incomplete.

### Fixed

- The image cleanup command in the deployment guide now applies the policy, using `--no-dry-run`.

### Changed

- The grid area now extends past London by more than the search radius, so lookups at the edge can
  still see nearby zones.
- Flood data is now stored as 5 m grid files instead of database shapes. Surface water shapes are
  far too large for Supabase's free 500 MB limit, while the grid files are only a few MB.
- The flood data test builds the grids, then checks size, speed and accuracy against the original
  shapes at known places and 250 random points. It no longer needs a database.

### Fixed

- Pinned dependencies so they install on Python 3.11, and CI now tests both 3.11 and 3.13.
