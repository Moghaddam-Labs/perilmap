# Changelog

All notable changes to PerilMap are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


### Added

- A privacy page. It explains what happens to a search, that there are no cookies or tracking, what
  each outside service (Vercel, Google Cloud, postcodes.io and OpenFreeMap) can see, how heavy use is
  limited, and who to contact.
- An About the data page, covering what PerilMap can and can't tell you, how each result is worked
  out, what each gap label means, what isn't covered, every data source with its date, and official
  checks to make.
- A flood insurance page explaining Flood Re: who it can help, why homes built from 2009 can't use
  it, Build Back Better, and what to ask an insurer, using Flood Re's own rules.
- A "Find out more" list under the results, linking to About the data, and to the flood insurance
  page when a flood zone is nearby.
- Flood zones on the map. After a check, the map shows the rivers and sea zones within 1 km of the
  spot, with the same patterns as the flood key, a circle for the search area and a key listing only
  the levels shown. Surface water, or no zones, can be chosen instead. Areas with no data are marked,
  so they can't look clear. The zones also appear in the printout.
- `POST /v1/zone-maps` in the API, which traces each flood level within the search area from the
  same grid squares the distances are measured from, so the map and the result cards always agree.
  Edges are smoothed by up to half a square. Each layer is fetched only when it's shown, which keeps
  checks themselves fast.
- Print or save the results as a PDF. The printout has a short report header with the location and
  date, an image of the map with the pin, every result with its sources open and link addresses
  written out, and the data credits. It always uses light colours, and results that are out of date
  because the pin moved can't be printed.
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
- Official Greater London boundary, with a check of surface water coverage against it.
- A list of blank surface water squares that show No data, so a gap can never look safe.
- Results outside London show Not available here yet, and results near a gap are marked may be
  incomplete.

### Changed

- The top bar now links to About the data and the new privacy page, and the footer links to all three
  new pages.
- API replies are now compressed, which shrinks zone maps to about a sixth of their size.
- CI can now be started by hand from the Actions tab ("Run workflow"), for when GitHub doesn't
  start a run after a merge.
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
- The grid area now extends past London by more than the search radius, so lookups at the edge can
  still see nearby zones.
- Flood data is now stored as 5 m grid files instead of database shapes. Surface water shapes are
  far too large for Supabase's free 500 MB limit, while the grid files are only a few MB.
- The flood data test builds the grids, then checks size, speed and accuracy against the original
  shapes at known places and 250 random points. It no longer needs a database.

### Fixed

- Notices now keep the class they're given, so error messages are left off printouts as intended.
- The website's lint tools now use minimatch 11.0.5, which fixes a moderate denial of service
  advisory (GHSA-g3hv-75wg-m249). ESLint and typescript-eslint still ask for version 10, so an npm
  override sets it until they catch up. It only affects development tools, not the live site.
- In dark mode, the print button now prints the light map. It switches the map to its light style,
  waits for it to draw, copies it, then switches back.
- The image cleanup command in the deployment guide now applies the policy, using `--no-dry-run`.
- Pinned dependencies so they install on Python 3.11, and CI now tests both 3.11 and 3.13.

