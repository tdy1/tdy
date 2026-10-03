# TECHA Engine

**TECHA — SIMULATE BEFORE YOU CAPITALIZE.**

TECHA is the engineering backbone for the Global Business Lab simulation system. It models business cases using explicit assumptions, evidence classifications, scenarios, sensitivities, multi-currency presentation, and reproducible financial calculations.

## Engineering principles

- Calculations are performed in a declared base currency; presentation currencies are separate.
- Every material input has an evidence classification and can be traced to its source or assumption.
- Missing primary evidence does not silently become a verified fact.
- Scenario and sensitivity changes are explicit and reproducible.
- Financial-engine regression tests protect previously validated calculations.
- Audit records describe what was calculated, with which assumptions, and when.
- No secrets, credentials, or private evidence belong in source control.

## Repository status

The repository contains the TECHA engine foundation and the first Business Simulation Workspace. Existing project decisions and completed work are treated as requirements; the repository does not intentionally repeat previously completed analytical work.

## Business Simulation Workspace

Run the application and open / to use the first user-facing workflow:

GBL Home → Business Case → Governance & Evidence → Scenarios → Simulation → Results → Audit / Integrity

For the GBL production workflow: Load GBL contract → review governance/evidence → select scenario → simulate → reconcile TECHA results against preserved GBL source results → inspect audit integrity → export.

The workspace creates and loads business cases through the existing API, records editable assumptions with explicit evidence classification, executes the deterministic simulation engine, and displays the resulting financial outputs. It is an application layer over the engine rather than a second financial calculator.

## Architecture

- techa/core/ — domain models, scenarios, execution and evidence
- techa/financial/ — financial calculations, cash flow, debt and currency handling
- techa/audit/ — reproducibility and audit records
- techa/storage/ — SQLite persistence
- techa/web/ — Business Simulation Workspace
- tests/ — unit, API and regression tests
- docs/ — architecture and governance documentation
- .github/workflows/ — continuous integration

## Local development

Requires Python 3.11+.

python -m pytest

The engine remains dependency-light so its numerical behavior is transparent and portable.
