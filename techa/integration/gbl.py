from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass


CONTRACT_VERSION = "1.0"
REQUIRED_TOP_LEVEL = {"contract_version", "business", "governance", "currency", "assumptions", "scenarios", "source_results"}


@dataclass(frozen=True)
class GBLSourceResult:
    result_id: str
    result_version: str
    source_system: str
    source_reference: str
    status: str


@dataclass(frozen=True)
class GBLCase:
    business_case: BusinessCase
    business_metadata: Mapping[str, Any]
    governance: Mapping[str, Any]
    presentation_currency: str | None
    fx_as_of: str | None
    fx_source: str | None
    scenarios: tuple[Mapping[str, Any], ...]
    source_results: tuple[GBLSourceResult, ...]


class GBLCaseValidationError(ValueError):
    pass


def _required(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "":
        raise GBLCaseValidationError(f"Missing required field: {context}.{key}")
    return value


def _validate_currency(code: str, field: str) -> str:
    try:
        return Currency(code, code).code
    except ValueError as exc:
        raise GBLCaseValidationError(f"Invalid currency: {field}") from exc


def validate_gbl_case(payload: Mapping[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL - set(payload)
    if missing:
        raise GBLCaseValidationError(f"Missing top-level fields: {', '.join(sorted(missing))}")
    if payload["contract_version"] != CONTRACT_VERSION:
        raise GBLCaseValidationError(f"Unsupported contract version: {payload['contract_version']}")

    business = payload["business"]
    governance = payload["governance"]
    currency = payload["currency"]
    if not isinstance(business, Mapping) or not isinstance(governance, Mapping) or not isinstance(currency, Mapping):
        raise GBLCaseValidationError("business, governance, and currency must be objects")

    for key in ("business_id", "name", "sector", "geography"):
        _required(business, key, "business")
    for key in ("state", "human_gate", "steps_frozen_through"):
        _required(governance, key, "governance")
    base_currency = _validate_currency(_required(currency, "base_currency", "currency"), "base_currency")

    assumptions = payload["assumptions"]
    if not isinstance(assumptions, list):
        raise GBLCaseValidationError("assumptions must be an array")
    seen: set[str] = set()
    valid_classes = {item.value for item in EvidenceClass}
    for item in assumptions:
        if not isinstance(item, Mapping):
            raise GBLCaseValidationError("Each assumption must be an object")
        for key in ("key", "value", "unit", "evidence_class", "source", "editable"):
            _required(item, key, "assumption")
        key = str(item["key"])
        if key in seen:
            raise GBLCaseValidationError(f"Duplicate assumption key: {key}")
        seen.add(key)
        if item["evidence_class"] not in valid_classes:
            raise GBLCaseValidationError(f"Invalid evidence class: {item['evidence_class']}")
        try:
            Decimal(str(item["value"]))
        except Exception as exc:
            raise GBLCaseValidationError(f"Invalid decimal value for assumption: {key}") from exc

    scenarios = payload["scenarios"]
    if not isinstance(scenarios, list):
        raise GBLCaseValidationError("scenarios must be an array")
    for scenario in scenarios:
        if not isinstance(scenario, Mapping):
            raise GBLCaseValidationError("Each scenario must be an object")
        overrides = _required(scenario, "overrides", "scenario")
        if not isinstance(overrides, Mapping):
            raise GBLCaseValidationError("scenario.overrides must be an object")
        unknown = set(overrides) - seen
        if unknown:
            raise GBLCaseValidationError(f"Scenario references unknown assumptions: {', '.join(sorted(unknown))}")

    presentation = currency.get("presentation_currency")
    fx_as_of = currency.get("fx_as_of")
    fx_source = currency.get("fx_source")
    if presentation is not None:
        presentation = _validate_currency(presentation, "presentation_currency")
        if presentation != base_currency and (not fx_as_of or not fx_source):
            raise GBLCaseValidationError("Different presentation currency requires fx_as_of and fx_source")

    source_results = payload["source_results"]
    if not isinstance(source_results, list):
        raise GBLCaseValidationError("source_results must be an array")
    result_ids: set[str] = set()
    for result in source_results:
        if not isinstance(result, Mapping):
            raise GBLCaseValidationError("Each source result must be an object")
        for key in ("result_id", "result_version", "source_system", "source_reference", "status"):
            _required(result, key, "source_result")
        if result["result_id"] in result_ids:
            raise GBLCaseValidationError(f"Duplicate source result ID: {result["result_id"]}")
        result_ids.add(result["result_id"])


def import_gbl_case(payload: Mapping[str, Any]) -> GBLCase:
    validate_gbl_case(payload)
    business = payload["business"]
    governance = payload["governance"]
    currency = payload["currency"]

    assumptions = {
        item["key"]: Assumption(
            key=item["key"],
            value=Decimal(str(item["value"])),
            unit=item["unit"],
            evidence_class=EvidenceClass(item["evidence_class"]),
            source=item["source"],
            editable=bool(item["editable"]),
        )
        for item in payload["assumptions"]
    }

    source_results = tuple(
        GBLSourceResult(
            result_id=item["result_id"],
            result_version=item["result_version"],
            source_system=item["source_system"],
            source_reference=item["source_reference"],
            status=item["status"],
        )
        for item in payload["source_results"]
    )

    return GBLCase(
        business_case=BusinessCase(
            case_id=str(business["business_id"]),
            name=str(business["name"]),
            base_currency=Currency(currency["base_currency"], currency["base_currency"]),
            assumptions=assumptions,
        ),
        business_metadata=dict(business),
        governance=dict(governance),
        presentation_currency=currency.get("presentation_currency"),
        fx_as_of=currency.get("fx_as_of"),
        fx_source=currency.get("fx_source"),
        scenarios=tuple(payload["scenarios"]),
        source_results=source_results,
    )


def export_gbl_case(case: GBLCase, contract_version: str = CONTRACT_VERSION) -> dict[str, Any]:
    if contract_version != CONTRACT_VERSION:
        raise GBLCaseValidationError(f"Unsupported contract version: {contract_version}")
    return {
        "contract_version": contract_version,
        "business": {
            "business_id": case.business_case.case_id,
            "name": case.business_case.name,
            "sector": case.business_metadata["sector"],
            "geography": case.business_metadata["geography"],
        },
        "governance": dict(case.governance),
        "currency": {
            "base_currency": case.business_case.base_currency.code,
            **({"presentation_currency": case.presentation_currency} if case.presentation_currency else {}),
            **({"fx_as_of": case.fx_as_of} if case.fx_as_of else {}),
            **({"fx_source": case.fx_source} if case.fx_source else {}),
        },
        "assumptions": [
            {"key": a.key, "value": str(a.value), "unit": a.unit, "evidence_class": a.evidence_class.value, "source": a.source, "editable": a.editable}
            for a in case.business_case.assumptions.values()
        ],
        "scenarios": [dict(s) for s in case.scenarios],
        "source_results": [r.__dict__.copy() for r in case.source_results],
    }
