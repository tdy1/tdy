# Global Business Lab Integration Mapping

## Purpose

This document defines how a Global Business Lab business case maps into TECHA without hard-coding a particular business into the engine.

TECHA remains the generic simulation engine and governance layer. GBL remains the business-analysis framework and evidence workflow.

## Canonical mapping

| GBL concept | TECHA representation | Rule |
|---|---|---|
| Business ID | `BusinessCase.case_id` | Stable GBL business identifier |
| Business name | `BusinessCase.name` | Descriptive business title |
| Calculation currency | `BusinessCase.base_currency` | One authoritative calculation currency |
| Financial input | `Assumption` | Explicit value, unit, evidence class, source |
| Evidence status | `EvidenceClass` / `EvidenceRegistry` | Never silently promote an assumption |
| Primary-verification blocker | Blocking evidence item | Prevent execution when classified as requiring primary verification or field validation |
| Scenario | `Scenario` | Overrides selected assumptions without changing the base case |
| One-way sensitivity | Sensitivity service | Variable and test values remain explicit |
| Presentation currency | Currency presentation layer | Conversion occurs after base-currency calculation |
| FX evidence | `FxRate` | Exact dated rate and source |
| Audit event | `AuditRecord` | Material execution/governance actions are digest-recorded |
| GBL analytical conclusion | External/reporting layer | Conclusions do not become financial inputs unless explicitly represented as assumptions |

## Business #548 mapping

Business #548 (Dehydrated Vegetable Production) is a reference/use-case dataset. Its completed calculations must not be rebuilt merely to populate TECHA.

The existing #548 governance state maps conceptually as follows:

- Business ID: `548`
- Business name: Dehydrated Vegetable Production
- Sector: Agriculture & Agribusiness
- Geography: Ethiopia, Addis Ababa / Modjo Regional Corridor
- Governance state: State 0; Human Gate 1 HOLD / NOT CLEARED
- Base financial calculations: ETB
- Presentation currency: independent from the calculation currency
- S1/S2/S3: separate GBL scales/scenarios
- Assumptions: imported only when intentionally mapped, retaining their original evidence classification
- Step 21 unresolved items: remain non-executable where their governing evidence class requires primary verification
- Completed #548 financial results: remain authoritative external reference results unless an explicit import/reconciliation fixture is created

## Scale and scenario rule

GBL scales such as S1, S2, and S3 should be represented as scenario/configuration data, not separate financial engines.

A scenario may override inputs such as capacity, utilization, selling price, raw-material cost, operating expense, or financing terms. The engine must calculate each scenario deterministically from its resolved inputs.

## Evidence rule

GBL evidence labels map to TECHA evidence classes:

- VERIFIED_FACT
- INDICATIVE_OBSERVED_DATA
- COST_ENGINEERING_ESTIMATE
- MARKET_ASSUMPTION
- ANALYTICAL_CONCLUSION
- REQUIRES_PRIMARY_VERIFICATION
- FIELD_VALIDATION_REQUIREMENTS

The last two classes are execution blockers in the current governance implementation.

This means a GBL case can remain analytically useful while still being correctly blocked from an executable simulation when a required primary/field verification item is unresolved.

## Currency rule

GBL may present a case in USD, ETB, KES, TZS, UGX, or another supported three-letter code.

The calculation remains in the case's authoritative base currency. Presentation conversion requires an exact dated FX rate when the presentation currency differs.

No implicit latest FX rate is permitted.

## Integration boundary

The first integration should be an explicit case-data mapping/import layer. It should not:

1. hard-code Business #548 into the financial engine;
2. duplicate financial formulas;
3. silently convert evidence classes;
4. overwrite authoritative GBL results;
5. create a second parallel currency calculation engine.

## Next implementation requirement

Before importing a production GBL case, define a versioned case-data contract covering:

1. business metadata;
2. assumption keys and units;
3. evidence IDs/classes and sources;
4. scenario definitions;
5. financial-input mapping;
6. currency and FX metadata;
7. governance state;
8. source-result reconciliation identifiers.

The contract should be tested with Business #548 as the first integration fixture, without recalculating or altering its authoritative completed results.
