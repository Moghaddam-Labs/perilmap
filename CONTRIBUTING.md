# Contributing

PerilMap is proprietary and is not open to outside contributions at the moment. The code is public
to view, and the [licence](LICENSE) explains what that does and doesn't allow.

Bug reports and data corrections are welcome as GitHub issues. Please report security problems
privately, as described in the [security policy](SECURITY.md).

## Working standards

- Work on a short-lived branch and merge through a pull request with green checks.
- Name branches by type, such as `feat/flood-data-test` or `fix/size-guard`.
- Run `ruff check .`, `ruff format --check .` and `pytest` before opening a pull request.
- Add a line to `CHANGELOG.md` for any notable change.
