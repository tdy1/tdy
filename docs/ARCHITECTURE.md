# TECHA Engine Architecture

## Layer 1 — Domain

Defines business cases, assumptions, evidence classes, currencies, and FX rates.

## Layer 2 — Financial engine

Performs deterministic calculations in the declared base currency. Presentation conversion is a separate operation.

The engine protects the mandatory direct-COGS reserve concept and prevents implicit FX conversion.

## Layer 3 — Audit

Records engine event, case identifier, engine version, inputs, outputs, timestamp, and SHA-256 digest.

Currency presentation is audited with the selected base/presentation currencies, exact as-of date, source, stored rate, and whether the rate was applied directly or inversely.

## Layer 4 — Application

The web/API layer consumes the domain and engine layers. It must not duplicate financial formulas.

The financial endpoint calculates once in the base currency, then optionally presents the resulting financial fields in a separately selected currency.

## Layer 5 — Verification

Unit, integration, financial regression, reconciliation, and configuration tests belong here. Existing validated financial results must be encoded as regression fixtures when their authoritative source is available.

## Evidence architecture

Inputs retain their evidence class. The engine does not promote an assumption to a verified fact. Evidence status is metadata governing interpretation, not a numerical adjustment.

## Scenario, sensitivity, and audit execution

Scenarios execute through the frozen financial engine. One-way sensitivity is a first-class service that creates reproducible scenario executions and a parent sensitivity audit record. Audit history can be retrieved by business case without altering prior records.

## Currency architecture

A business case has one calculation base currency. Users may choose a presentation currency independently. Presentation conversion is explicit and occurs after calculation; it never changes the underlying financial result.

FX rates are persisted as dated, sourced observations. A presentation request must provide an exact as-of date when the presentation currency differs from the base currency. The API accepts either a stored direct pair or a stored inverse pair for that exact date. If an inverse pair is used, the converter divides by the stored rate; it does not invent or silently fetch a latest rate.

There is no implicit FX rate, averaging, silent currency substitution, or automatic latest-rate selection. The returned FX record identifies the stored pair/source, while the response also records whether the selected rate was direct or inverse.

## Release boundary

Currency selection, durable FX-rate persistence, direct/inverse presentation, audit capture, and browser controls are implemented. The remaining release gate is CI verification followed by release packaging; no previously completed analytical result is recomputed merely for migration.
