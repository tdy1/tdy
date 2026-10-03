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

## Evidence architecture

Inputs retain their evidence class. The engine does not promote an assumption to a verified fact. Evidence status is metadata governing interpretation, not a numerical adjustment.

## Scenario, sensitivity, and audit execution

Scenarios execute through the frozen financial engine. One-way sensitivity is a first-class service that creates reproducible scenario executions and a parent sensitivity audit record. Audit history can be retrieved by business case without altering prior records.

## Currency architecture

A business case has one calculation base currency. Users may choose a presentation currency independently. Presentation conversion is explicit and occurs after calculation; it never changes the underlying financial result. Direct or inverse FX rates must be supplied with an as-of date and source. No implicit rate, averaging, or silent currency substitution is permitted.

## Next implementation boundary

The next boundary is durable FX-rate management and API-level currency selection/presentation, followed by release verification. No previously completed analytical result is recomputed merely for migration.
