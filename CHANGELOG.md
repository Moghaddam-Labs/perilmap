# Changelog

All notable changes to PerilMap are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repo foundations: README, licence, security policy, contribution notes, CI and Dependabot.
- Flood data test: estimates London's Environment Agency flood data, loads it into PostGIS with a
  size guard, and reports database size, lookup speed and results for 20 known places.

### Fixed

- Pinned dependencies so they install on Python 3.11, and CI now tests both 3.11 and 3.13.
