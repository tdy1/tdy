from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from threading import RLock

from techa.audit.record import AuditRecord
from techa.core.models import Assumption, BusinessCase, Currency, EvidenceClass, FxRate


class SQLiteStore:
    """Small persistence adapter safe for FastAPI's worker-thread execution."""

    def __init__(self, path: str | Path) -> None:
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute("PRAGMA foreign_keys=ON")
        self._lock = RLock()

    def initialize(self, schema_path: str | Path) -> None:
        with self._lock:
            self.db.executescript(Path(schema_path).read_text(encoding="utf-8"))
            self.db.commit()

    def save_business_case(self, case: BusinessCase) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self.db.execute(
                """INSERT INTO business_case(case_id,name,base_currency,created_at,updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(case_id) DO UPDATE SET name=excluded.name,
                   base_currency=excluded.base_currency, updated_at=excluded.updated_at""",
                (case.case_id, case.name, case.base_currency.code, now, now),
            )
            self.db.execute("DELETE FROM assumption WHERE case_id=?", (case.case_id,))
            self.db.executemany(
                """INSERT INTO assumption(case_id,key,value,unit,evidence_class,source,editable)
                   VALUES(?,?,?,?,?,?,?)""",
                [
                    (case.case_id, a.key, str(a.value), a.unit,
                     a.evidence_class.value, a.source, int(a.editable))
                    for a in case.assumptions.values()
                ],
            )
            self.db.commit()

    def get_business_case(self, case_id: str) -> BusinessCase | None:
        with self._lock:
            row = self.db.execute(
                "SELECT case_id,name,base_currency FROM business_case WHERE case_id=?",
                (case_id,),
            ).fetchone()
            if row is None:
                return None
            assumptions = {}
            for r in self.db.execute(
                "SELECT key,value,unit,evidence_class,source,editable "
                "FROM assumption WHERE case_id=? ORDER BY key",
                (case_id,),
            ):
                assumptions[r[0]] = Assumption(
                    key=r[0], value=Decimal(r[1]), unit=r[2],
                    evidence_class=EvidenceClass(r[3]), source=r[4],
                    editable=bool(r[5]),
                )
            return BusinessCase(
                case_id=row[0], name=row[1],
                base_currency=Currency(row[2], row[2]),
                assumptions=assumptions,
            )

    def save_gbl_case_metadata(self, case_id: str, contract_version: str, business_metadata: dict, governance: dict,
                               presentation_currency: str | None, fx_as_of: str | None,
                               fx_source: str | None, scenarios: list, source_results: list) -> None:
        with self._lock:
            self.db.execute(
                """INSERT INTO gbl_case_metadata
                   (case_id,business_metadata_json,contract_version,governance_json,presentation_currency,fx_as_of,fx_source,scenarios_json,source_results_json)
                   VALUES(?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(case_id) DO UPDATE SET business_metadata_json=excluded.business_metadata_json, contract_version=excluded.contract_version,
                   governance_json=excluded.governance_json,presentation_currency=excluded.presentation_currency,
                   fx_as_of=excluded.fx_as_of,fx_source=excluded.fx_source,scenarios_json=excluded.scenarios_json,
                   source_results_json=excluded.source_results_json""",
                (case_id, contract_version, json.dumps(business_metadata, sort_keys=True, default=str), json.dumps(governance, sort_keys=True, default=str),
                 presentation_currency, fx_as_of, fx_source,
                 json.dumps(scenarios, sort_keys=True, default=str),
                 json.dumps(source_results, sort_keys=True, default=lambda o: o.__dict__)),
            )
            self.db.commit()

    def get_gbl_case_metadata(self, case_id: str) -> dict | None:
        with self._lock:
            row = self.db.execute(
                "SELECT business_metadata_json,contract_version,governance_json,presentation_currency,fx_as_of,fx_source,scenarios_json,source_results_json "
                "FROM gbl_case_metadata WHERE case_id=?", (case_id,)
            ).fetchone()
        if row is None:
            return None
        return {
            "business_metadata": json.loads(row[0]), "contract_version": row[1], "governance": json.loads(row[2]),
            "presentation_currency": row[3], "fx_as_of": row[4], "fx_source": row[5],
            "scenarios": json.loads(row[6]), "source_results": json.loads(row[7]),
        }

    def save_fx_rate(self, fx: FxRate) -> None:
        with self._lock:
            self.db.execute(
                "INSERT OR REPLACE INTO fx_rate "
                "(from_currency,to_currency,rate,as_of,source) VALUES(?,?,?,?,?)",
                (fx.from_currency.upper(), fx.to_currency.upper(), str(fx.rate),
                 fx.as_of, fx.source),
            )
            self.db.commit()

    def get_fx_rate(self, from_currency: str, to_currency: str, as_of: str) -> FxRate | None:
        source = from_currency.upper()
        target = to_currency.upper()
        with self._lock:
            row = self.db.execute(
                "SELECT from_currency,to_currency,rate,as_of,source "
                "FROM fx_rate WHERE from_currency=? AND to_currency=? AND as_of=?",
                (source, target, as_of),
            ).fetchone()
        if row is None:
            return None
        return FxRate(
            from_currency=row[0], to_currency=row[1],
            rate=Decimal(row[2]), as_of=row[3], source=row[4],
        )

    def save_audit_record(self, record: AuditRecord) -> None:
        payload = json.dumps(
            {"inputs": record.inputs, "outputs": record.outputs},
            sort_keys=True, default=str,
        )
        with self._lock:
            self.db.execute(
                "INSERT OR REPLACE INTO audit_record "
                "(digest,event,case_id,engine_version,recorded_at,payload_json) "
                "VALUES(?,?,?,?,?,?)",
                (record.digest(), record.event, record.case_id,
                 record.engine_version, record.recorded_at, payload),
            )
            self.db.commit()

    def get_audit_records(self, case_id: str, limit: int = 100) -> list[dict[str, str]]:
        if limit < 1 or limit > 1000:
            raise ValueError("Audit limit must be between 1 and 1000")
        with self._lock:
            rows = self.db.execute(
                "SELECT digest,event,case_id,engine_version,recorded_at,payload_json "
                "FROM audit_record WHERE case_id=? ORDER BY recorded_at DESC LIMIT ?",
                (case_id, limit),
            ).fetchall()
        return [
            {
                "digest": row[0], "event": row[1], "case_id": row[2],
                "engine_version": row[3], "recorded_at": row[4], "payload_json": row[5],
            }
            for row in rows
        ]

    def close(self) -> None:
        with self._lock:
            self.db.close()
