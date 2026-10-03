# TECHA v0.1.0 — Final Release Manifest

## Status

**ENGINEERING FROZEN**

TECHA v0.1.0 is the frozen executable baseline for the first production-oriented Global Business Lab integration.

## Frozen scope

- Deterministic financial engine
- Mandatory direct COGS reserve
- Explicit base/presentation currency architecture
- Exact-date FX
- Scenario execution and sensitivity
- Cash-flow and debt foundations
- Evidence classification and execution gate
- Audit trail and persisted SHA-256 integrity verification
- GBL Case Contract v1
- GBL import/export and source-result preservation
- Business #548 integration fixture boundary
- Business Universe
- Governed Business Intake
- Active Case navigation
- Governance-first Case Summary
- Execution Readiness distinct from Investment Clearance
- Results reconciliation
- Browser Business Simulation Workspace
- SQLite persistence
- Docker deployment
- Automated Python regression and Docker smoke verification

## Architectural boundaries

Business #548 remains a reference/use-case fixture. Its authoritative workbook results are not silently recalculated or replaced by TECHA.

GBL governance metadata is preserved when a GBL contract is imported. An intake-created case may exist before a GBL contract is imported; the workspace explicitly reports that state.

Presentation currency never becomes a second calculation engine.

## Verification

The final baseline is accepted only on green CI, including the Docker build/smoke job.

## Deployment

Canonical deployment:

    docker build -t techa .
    docker run --rm -p 8000:8000 techa

Open:

    http://127.0.0.1:8000/

## Post-freeze rule

Any change after this manifest requires an explicit post-freeze change decision and a new CI verification cycle.

## Administrative note

A formal GitHub tag/release object is not claimed as published because the connected GitHub interface does not expose tag/release creation. The repository commit containing this manifest is the engineering freeze baseline.
