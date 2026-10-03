# TECHA Release Procedure

1. Run the complete CI test suite.
2. Verify financial regression fixtures.
3. Review architecture and implementation status.
4. Update the semantic version in `techa/__init__.py` and `pyproject.toml`.
5. Update CHANGELOG.md.
6. Create a Git tag matching the version.
7. Publish the release only after CI is green.

A release is not considered final merely because the application starts. Financial, audit, persistence, API, security and regression checks must all pass.
