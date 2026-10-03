# TECHA → GBL Production Integration Plan v1

## Purpose

Turn the existing TECHA Engine + GBL contract integration into the execution platform for Global Business Lab (GBL).

GBL remains the governing methodology and source of business definitions, evidence, scenarios, governance states, and authoritative source results. TECHA provides execution, persistence, financial calculation, sensitivity analysis, currency presentation, auditability, and the application workspace.

## Non-negotiable boundaries

1. GBL methodology is not replaced by TECHA.
2. TECHA financial logic remains generic; Business #548 is never hard-coded into the engine.
3. Imported GBL source results remain source results; TECHA does not silently recalculate or overwrite them.
4. Evidence classes are preserved exactly. Import never promotes evidence.
5. Blocking evidence remains blocking until explicitly reclassified through an audited action.
6. Calculation currency is authoritative; presentation currency is a separate dated-FX layer.
7. Conclusions are reporting outputs, not hidden financial inputs.
8. No universal feasibility/compliance score is introduced.
9. Primary verification requirements remain visible even when a State 0 simulation is executable.
10. Existing completed engine behavior is regression-protected.

## Production operating model

### A. Business Universe
GBL supplies canonical business identity and classification. TECHA stores and operates on an individual governed Business Case.

Minimum identity: business_id, business name, sector, geography, governance state, human gate, steps frozen through.

### B. Business Intake
A business can enter TECHA through either an imported GBL Case Contract v1 or the governed Business Universe intake path.

The Business Universe path creates an executable Business Case, assigns the explicit calculation currency, links the active case to the canonical business identity, advances lifecycle through CANDIDATE → INGESTED, and records a `gbl.business.intake` audit event.

Contract intake validates identity, evidence classes, governance, scenarios, currency, and source-result reconciliation.

Neither intake path promotes evidence, silently changes governance, recalculates authoritative source results, infers missing FX, or replaces source-result identity.

### C. Governance Workspace
Governance is visible before simulation: State, Human Gate, frozen-through step, blockers, evidence counts, executable status, source-result status, and case-level identity/currency summary. The workspace distinguishes execution readiness from investment clearance.

### D. Scenario Workspace
GBL scenarios become first-class executable configurations. Initial model: S1, S2, S3, explicit overrides, scenario-level execution audit. The generic engine remains unaware of #548-specific meanings.

### E. Evidence Workspace
Each assumption exposes value, unit, evidence class, source, editable flag, blocking status, and executable status. Reclassification requires an explicit audited action.

### F. Simulation Workspace
Execution sequence:
Business Case → Governance check → Evidence gate → Scenario selection → Financial engine → Presentation currency → Audit record → Result.

### G. Results Workspace
Results distinguish TECHA-calculated simulation results, imported GBL source results, analytical interpretation, and unresolved verification requirements. These must not be visually conflated.

### H. Audit / Integrity
Material state-changing operations receive audit records. Minimum events: gbl.case_imported, gbl.case_exported, simulation.execute, sensitivity.executed, evidence.reclassified, currency.presented.

## Production UI information architecture

The current five-step TECHA workspace becomes the execution surface inside a broader GBL shell:

1. **GBL Home** — Business Universe, case intake, governance-first case summary, and recent-case navigation.
2. **Business Case** — Identity, Governance, Scenarios, Source Results.
3. **Evidence & Assumptions** — Assumptions, evidence classes, blocking items, verification requirements.
4. **Simulation** — Scenario, financial inputs, calculation currency, presentation currency, FX date.
5. **Results** — Key metrics, scenario result, sensitivity, source-result reconciliation.
6. **Audit** — Event history, digests, execution lineage.

## First production acceptance case

Business #548 is the first integration case because its GBL contract already exists.

Acceptance must prove:
- identity preserved
- State 0 / Human Gate 1 HOLD preserved
- Steps 1–55 frozen-through preserved
- S1/S2/S3 scenarios preserved
- evidence classifications preserved
- source-result identity preserved
- source results are not overwritten
- TECHA executes according to the evidence gate
- presentation currency remains independent from calculation currency
- audit lineage is generated

The #548 case is an integration fixture/use case, not engine-specific logic.

## Business Universe → Intake → Case Lifecycle

The Business Universe is the canonical registry layer. Creating a universe item does not constitute investment clearance or feasibility approval.

The governed lifecycle currently implemented is:

`UNIVERSE → CANDIDATE → INGESTED → GOVERNANCE_HOLD / SIMULATION_READY → SIMULATED → REVIEW → CLEARED / NOT_CLEARED`

Lifecycle transitions are explicit and audited. The lifecycle map is an implementation control and remains subject to formal GBL governance review; it is not silently treated as a new frozen methodological step.

The Business Intake operation is deliberately separate from investment clearance: it creates the executable case and establishes lineage, while evidence gates and Human Gate controls continue to govern simulation and investment decisions.

## Versioning boundary

The existing 0.1.0 engine baseline remains the stable foundation. Production integration is a separately documented phase. No release/tag claim is made until corresponding formal GitHub release metadata exists.

## Implementation sequence

### P1 — Production contract/service layer
- governed case summary
- scenario listing
- evidence status
- source-result reconciliation
- explicit execution readiness

### P2 — Production workspace UI
- GBL shell
- case navigation
- governance-first presentation
- scenario/evidence/results views

### P3 — #548 acceptance
- import
- inspect
- execute permitted cases
- reconcile source results
- audit

### P4 — Hardening
- API tests
- UI regression tests
- Docker verification
- documentation
- release readiness
- readiness/reconciliation/integrity UI hardening
- persisted audit-digest verification endpoint and workspace integrity verification

**Current status:** P0–P3 complete. P4 engineering hardening is complete and CI is green. The only remaining release-readiness item is formal GitHub tag/release publication, which the connected GitHub interface does not expose. Formal GitHub tag/release publication remains pending because the connected GitHub interface does not expose tag/release creation.
