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

This repository is being established as the canonical TECHA engineering repository. Existing project decisions and completed work are treated as requirements; this repository does not intentionally repeat previously completed analytical work.

## Initial architecture

- `techa/core/` — domain models and engines
- `techa/financial/` — financial calculations and currency handling
- `techa/audit/` — reproducibility and audit records
- `tests/` — unit and regression tests
- `docs/` — architecture and governance documentation
- `.github/workflows/` — continuous integration

## Local development

Requires Python 3.11+.

```bash
python -m pytest
```

The initial engine is intentionally dependency-light so its numerical behavior remains transparent and portable.
