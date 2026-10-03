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
    for result in source_results:
        if not isinstance(result, Mapping):
            raise GBLCaseValidationError("Each source result must be an object")
        for key in ("result_id", "result_version", "source_system", "source_reference", "status"):
            _required(result, key, "source_result")


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
        governance=dict(governance),
        presentation_currency=currency.get("presentation_currency"),
        fx_as_of=currency.get("fx_as_of"),
        fx_source=currency.get("fx_source"),
        scenarios=tuple(payload["scenarios"]),
        source_results=source_results,
    )
