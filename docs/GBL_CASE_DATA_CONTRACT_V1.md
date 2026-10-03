# GBL Case Data Contract v1

## Status

Version 1 is the first integration contract between Global Business Lab case data and TECHA.

It is a transport/mapping contract, not a financial model. It does not contain Business #548's calculated results and does not duplicate TECHA formulas.

## Required top-level structure

```json
{
  "contract_version": "1.0",
  "business": {},
  "governance": {},
  "currency": {},
  "assumptions": [],
  "scenarios": [],
  "source_results": []
}
```

## Business metadata

Required:

- `business_id`: stable GBL identifier
- `name`
- `sector`
- `geography`

Optional descriptive fields must not affect financial calculations unless explicitly mapped as assumptions.

## Governance

Required:

- `state`
- `human_gate`
- `steps_frozen_through`

Optional:

- `blocking_reasons`
- `governance_note`

Governance metadata must survive import unchanged.

## Currency

Required:

- `base_currency`: authoritative calculation currency

Optional:

- `presentation_currency`
- `fx_as_of`
- `fx_source`

A different presentation currency requires an exact dated FX rate at execution time.

## Assumption record

Each assumption contains:

- `key`
- `value`
- `unit`
- `evidence_class`
- `source`
- `editable`

The evidence class must be one of TECHA's seven canonical evidence classes. No importer may silently reclassify evidence.

## Scenario record

Each scenario contains:

- `scenario_id`
- `name`
- `overrides`

Overrides reference existing assumption keys. A scenario does not create a second financial engine.

## Source-result reconciliation

Completed GBL results may be referenced using:

- `result_id`
- `result_version`
- `source_system`
- `source_reference`
- `status`

A source result is evidence/reference data. Importing it must not imply that TECHA independently reproduced it.

## Business #548 fixture policy

Business #548 is the first integration fixture.

Its completed GBL calculations remain authoritative reference outputs. The fixture should initially validate:

1. metadata preservation;
2. assumption/evidence preservation;
3. S1/S2/S3 scenario mapping;
4. governance-state preservation;
5. currency metadata;
6. source-result identity/reconciliation.

It must **not** recalculate #548 merely to validate the transport contract.

## Import invariants

An importer must reject:

- missing business ID;
- missing base currency;
- invalid evidence class;
- duplicate assumption keys;
- scenario overrides for unknown assumption keys;
- non-positive or undated FX records when FX is required;
- missing governance state;
- malformed source-result identifiers.

An importer must never:

- promote MARKET_ASSUMPTION to VERIFIED_FACT;
- convert REQUIRES_PRIMARY_VERIFICATION into an executable class;
- replace an existing authoritative result;
- substitute an implicit/latest FX rate;
- modify source financial results.

## Versioning

Backward-compatible additions increment the minor version (1.x).

Breaking changes increment the major version (2.0+).

Every imported case must retain its contract version for auditability.
