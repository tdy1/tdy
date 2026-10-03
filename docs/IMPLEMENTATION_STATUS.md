# TECHA Implementation Status

## Current state

The canonical TECHA repository contains the first production-oriented engine foundation plus durable multi-currency presentation. Work is being added only for identified implementation gaps; completed analytical work is not recomputed or replaced.

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
- Durable dated FX-rate API
- Exact-date direct and inverse FX presentation
- Currency-presentation audit capture
- Browser base/presentation currency controls
- Docker and docker-compose deployment
- CI with GitHub Actions
- Unit/API/regression tests
- Security baseline
- Release procedure and changelog

### Currency design decision

TECHA uses **one calculation base currency per business case, with an independent presentation currency**. This is deliberately different from maintaining parallel financial calculations in ETB, USD, EUR, KES, TZS, UGX, etc.

The financial engine remains currency-neutral: it calculates the business case in its declared base currency. Presentation conversion is a separate, auditable layer. This prevents exchange-rate changes from altering the underlying model and avoids duplicated financial logic.

The architecture supports arbitrary three-letter currency codes. The browser currently exposes the initial operational set ETB, USD, EUR, KES, TZS, and UGX; the engine/API are not limited to that list.

### Verification

The latest GitHub Actions run for the corrected presentation-precision regression is green. Release verification must continue to include any subsequent implementation commits.

Previously completed GBL and Business #548 calculations remain external reference requirements until their authoritative fixtures are intentionally imported. They are not recreated here merely to populate the repository.
