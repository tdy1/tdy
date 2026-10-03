# TECHA Engine Architecture

## Layer 1 — Domain

Defines business cases, assumptions, evidence classes, currencies, and FX rates.

## Layer 2 — Financial engine

Performs deterministic calculations in the declared base currency. Presentation conversion is a separate operation.

The engine currently protects the mandatory direct-COGS reserve concept and prevents implicit FX conversion.

## Layer 3 — Audit

Records engine event, case identifier, engine version, inputs, outputs, timestamp, and SHA-256 digest.

## Layer 4 — Application

The web/API layer will consume the domain and engine layers. It must not duplicate financial formulas.

## Layer 5 — Verification

Unit, integration, financial regression, reconciliation, and configuration tests belong here. Existing validated financial results must be encoded as regression fixtures when their authoritative source is available.

## Currency architecture

A business case has one calculation base currency. Users may choose presentation currency independently. FX rates are explicit data with an as-of date and source. The system must never silently replace an assumption currency or apply an undocumented exchange rate.

## Evidence architecture

Inputs retain their evidence class. The engine does not promote an assumption to a verified fact. Evidence status is metadata governing interpretation, not a numerical adjustment.

## Next implementation boundary

The next build layer is the scenario/sensitivity engine, followed by API/application services and persisted case storage. No previously completed analytical result is recomputed merely for the sake of migration.
