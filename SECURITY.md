# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately, using
[GitHub's private vulnerability reporting](https://github.com/Moghaddam-Labs/perilmap/security/advisories/new).
Don't open a public issue. I aim to reply within 7 days.

## Supported versions

PerilMap is at the planning stage and has no released versions. Fixes go to the `main` branch.

## Handling secrets and personal data

- The API needs no credentials or database, and doesn't store searched locations or postcodes.
- Locations and postcodes aren't logged, and error replies don't repeat them.
- Any credentials added later stay in a local `.env` file, which Git ignores.
