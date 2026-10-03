# GBL ↔ TECHA Release Verification

## Scope

This document records the final engineering verification boundary for the first TECHA/Global Business Lab integration.

## Verified integration path

1. GBL Case Data Contract v1 is validated.
2. Business #548 is used as a transport/integration fixture, not embedded in the financial engine.
3. Import preserves business metadata, governance, evidence classes, scenarios, currency metadata, and source-result identity.
4. Persisted GBL metadata can be reloaded.
5. Export reconstructs the contract without replacing authoritative source results.
6. Import and export create audit records.
7. Duplicate source-result identifiers are rejected.
8. Blocking evidence remains blocking and prevents executable simulation.
9. Base-currency calculation remains authoritative; presentation currency is an independent dated-FX layer.
10. The browser workspace exposes explicit GBL load/export controls.
11. CI covers Python regression tests and Docker image build/smoke verification.

## Business #548 boundary

Business #548 (Dehydrated Vegetable Production) remains a GBL reference/use-case fixture. TECHA does not claim to independently reproduce the authoritative #548 workbook merely by importing its contract.

Its governance state, evidence classifications, scenarios, and source-result reconciliation identifiers are preserved as transport metadata.

## Browser regression boundary

The automated browser-surface regression verifies that the workspace HTML contains the required GBL controls and API routes. It is a structural smoke test, not a substitute for human browser acceptance testing.

## Docker verification boundary

CI builds the production Docker image and starts it, then checks the `/health` endpoint before the container is removed.

## Release-readiness checklist

- [x] Financial engine regression suite
- [x] Currency / dated FX controls
- [x] Evidence classification and blocking gate
- [x] Scenario and sensitivity execution
- [x] Audit trail
- [x] GBL contract validation
- [x] GBL import/persistence
- [x] GBL export
- [x] #548 integration fixture
- [x] Governance preservation
- [x] Scenario preservation
- [x] Source-result reconciliation
- [x] Browser workspace GBL controls
- [x] Docker build/smoke test added to CI
- [x] Execution-readiness UI state
- [x] TECHA-vs-GBL result reconciliation UI
- [x] Audit-integrity UI status
- [x] Persisted audit-digest integrity verification API and automated regression test
- [x] Final engineering freeze — TECHA v0.1.0 source, engine, workspace, tests, Docker verification, and GBL integration boundary frozen
- [ ] Formal Git tag/release publication — administrative only; current connected GitHub interface does not expose tag/release creation

## Final freeze status

Engineering work for TECHA v0.1.0 is frozen. No further feature work is required for the executable baseline. Changes after this point require an explicit post-freeze change decision and a new verification cycle.

The canonical executable deployment is the repository Docker image. The browser workspace is served by the FastAPI application at `/`.

## Important limitations

The current repository schema uses CREATE TABLE IF NOT EXISTS; it does not yet provide a general production migration framework for schema evolution.

The browser regression is structural rather than a full Playwright-style browser automation suite.

A formal GitHub release must only be reported as published after GitHub confirms creation of the tag/release object.
