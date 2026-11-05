# Changelog

All notable changes to PerilMap are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- README banner, with its map drawn from Environment Agency flood data for the Thames.
- Repo foundations: README, licence, security policy, contribution notes, CI and Dependabot.
- Flood data test: estimates London's Environment Agency flood data, loads it into PostGIS with a
  size guard, and reports database size, lookup speed and results for 20 known places.

### Added

- Official Greater London boundary, with a check of surface water coverage against it.
- A list of blank surface water squares that show No data, so a gap can never look safe.
- Results outside London show Not available here yet, and results near a gap are marked may be
  incomplete.

### Changed

- The grid area now extends past London by more than the search radius, so lookups at the edge can
  still see nearby zones.
- Flood data is now stored as 5 m grid files instead of database shapes. Surface water shapes are
  far too large for Supabase's free 500 MB limit, while the grid files are only a few MB.
- The flood data test builds the grids, then checks size, speed and accuracy against the original
  shapes at known places and 250 random points. It no longer needs a database.

### Fixed

- Pinned dependencies so they install on Python 3.11, and CI now tests both 3.11 and 3.13.
