# Changelog

All notable changes to PerilMap are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Bezel Charts is updated to v1.1.0, for its stacked bars and slanted labels.
- Every expandable line on the site shares one open and close arrow.
- "Flood levels you can tell apart" is now "Telling flood levels apart", so it fits on one line.
- The flood levels and data gaps explanations are now cards in a row under "Reading the results",
  with a new card for where the data comes from. Each opens on click or tap and closes when you click
  elsewhere, press Escape or open another.
- The results heading names the postcode, such as "What's around the pin near W5 4HT".
- The footer and the new sources card share one list of data sources, which a test keeps matched to
  the API.
- "How it works" is now three cards in a row, matching "What PerilMap looks at".
- The website's content security policy allows inline styles, which Bezel Charts needs. Scripts are
  still locked down.
- The website's main colour is now ink green, across the site, its icon, the README banner and the
  social preview.
- The home page has a slim top bar, room for postcode search at the top, a shorter header on phones,
  and new sections for what PerilMap looks at and how it works. The flood key and gap explanations
  now sit further down.
- Website styling: pill-shaped controls, softly rounded panels, and a labelled two-tone footer holding
  data credits, licences, project links and the privacy summary.

### Added

- A permanent chart on the home page of how much of each London borough is in a rivers and sea
  flood zone, stacked into Low or higher and Very Low. It uses vertical bars with slanted borough
  names on wide screens and horizontal bars on phones, with the figures as a table and a note on why
  a small share doesn't mean no risk. Worked out by `scripts/export_borough_flood.py`.
- A line under the results heading saying how recent each result's data is.
- Result cards for each peril at the pin, using the API's own wording: the summary, what it means,
  how sure it is, what you can do, links to official guidance and the data's source. Flood cards list
  the nearest zone of each level, and the heat card shows where the area sits in London's range with
  a Bezel Charts gauge. Results say when they're out of date because the pin has moved.
- Postcode search on the home page, using the API, with clear messages for every kind of problem.
- A map to put a pin on the home, which can be moved by clicking, dragging or the arrow keys, and
  says in words where the pin is. It shows the edge of Greater London, and still lets people carry
  on if the map can't load.
- Icons for each peril, ready for the result cards, with a neutral icon for future plug-ins.
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
