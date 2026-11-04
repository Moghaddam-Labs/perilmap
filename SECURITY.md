# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately, using
[GitHub's private vulnerability reporting](https://github.com/Moghaddam-Labs/perilmap/security/advisories/new).
Don't open a public issue. I aim to reply within 7 days.

## Supported versions

PerilMap is at the planning stage and has no released versions. Fixes go to the `main` branch.

## Handling secrets and personal data

- Database credentials stay in a local `.env` file, which Git ignores.
- Connection errors have the password removed before they're shown.
- The data test uses landmark locations only. It doesn't handle anyone's address.
