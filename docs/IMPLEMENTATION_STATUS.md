# TECHA Implementation Status

## Current state

The canonical TECHA repository now contains the complete first production-oriented engine foundation. Work was added only for previously identified gaps; completed analytical work was not recomputed or replaced.

### Implemented

- Domain/business-case and evidence classification model
- Explicit base-currency and presentation-FX architecture
- Deterministic financial calculation engine
- Mandatory direct-COGS reserve capability
- Multi-period cash-flow engine
- Working-capital treatment: AR + inventory - AP
- Debt amortization and interest schedule
- Scenario execution
- One-way sensitivity execution
- First-class sensitivity service and API
- Persisted audit-history retrieval
- Evidence registry
- Audit records with SHA-256 digest
- SQLite persistence schema/repository foundation
- FastAPI application layer
- Minimal browser UI for financial calculation
- Docker and docker-compose deployment
- CI with GitHub Actions
- Unit/API/regression tests
- Security baseline
- Release procedure and changelog

### Verification

GitHub Actions is the release verification gate. A recent sensitivity test cycle exposed incorrect test expectations for the financial engine's tax treatment; those expectations have been corrected. The newest CI cycle must be green before a release tag is considered final.

### Remaining release gate

The remaining item is release verification: allow the corrected CI cycle to complete, inspect any failures, correct them, and only then assign the next release version/tag.

Previously completed GBL and Business #548 calculations remain external reference requirements until their authoritative fixtures are intentionally imported. They are not recreated here merely to populate the repository.
