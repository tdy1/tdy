# TECHA Implementation Status

## Current state

The canonical TECHA repository contains the production-oriented engine foundation and the first user-facing Business Simulation Workspace. Work is added only for identified implementation gaps; completed analytical work is not recomputed or replaced.

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
- Workspace presentation-result context: displayed FX rate/date/source/direction and same-currency handling
- Business Simulation Workspace: create/load business case, edit assumptions, run base/scenario simulation, sensitivity, audit review, and view financial outputs
- Docker and docker-compose deployment
- CI with GitHub Actions
- Unit/API/regression tests
- Security baseline
- Release procedure and changelog

### Workspace boundary

The Business Simulation Workspace is intentionally an application layer over the existing engine. It does not duplicate financial formulas. Users create a business case, store explicit editable assumptions with an evidence class, and execute the case through the existing deterministic simulation service. Simulation execution produces an audit record.

The current workspace records financial inputs as MARKET_ASSUMPTION by default. This is a deliberate governance-safe starting point; later evidence workflows can promote or reclassify inputs only through explicit controls.

### Currency design decision

TECHA uses one calculation base currency per business case, with an independent presentation currency. The financial engine remains currency-neutral; presentation conversion is a separate, auditable layer.

The architecture supports arbitrary three-letter currency codes. The browser exposes the initial operational set ETB, USD, EUR, KES, TZS, and UGX; the engine/API are not limited to that list.

### Verification

The current `master` branch has passed the full GitHub Actions CI suite through **run #97** (`f5990e38def1c85f933ef2c288c347a1a6f4d46e`). The CI test job completed successfully using the repository's `pytest` suite. Runs #94, #95, #96, and #97 are all green.

The latest verified sequence covers workspace creation/loading, scenario execution, evidence status and reclassification, blocking governance, presentation currency, sensitivity execution, audit actions, and the same-currency presentation path.

Formal GitHub release/tag publication remains an administrative step separate from engineering verification.

Previously completed GBL and Business #548 calculations remain external reference requirements until their authoritative fixtures are intentionally imported. They are not recreated here merely to populate the repository.
