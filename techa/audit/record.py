from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class AuditRecord:
    event: str
    case_id: str
    engine_version: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    recorded_at: str

    @classmethod
    def create(
        cls,
        event: str,
        case_id: str,
        engine_version: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> "AuditRecord":
        return cls(
            event=event,
            case_id=case_id,
            engine_version=engine_version,
            inputs=inputs,
            outputs=outputs,
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )

    def digest(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
