CREATE TABLE IF NOT EXISTS business_case (
 case_id TEXT PRIMARY KEY, name TEXT NOT NULL, base_currency TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assumption (
 case_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, unit TEXT NOT NULL,
 evidence_class TEXT NOT NULL, source TEXT, editable INTEGER NOT NULL DEFAULT 1,
 PRIMARY KEY(case_id,key), FOREIGN KEY(case_id) REFERENCES business_case(case_id)
);
CREATE TABLE IF NOT EXISTS fx_rate (
 from_currency TEXT NOT NULL, to_currency TEXT NOT NULL, rate TEXT NOT NULL,
 as_of TEXT NOT NULL, source TEXT NOT NULL, PRIMARY KEY(from_currency,to_currency,as_of)
);
CREATE TABLE IF NOT EXISTS audit_record (
 digest TEXT PRIMARY KEY, event TEXT NOT NULL, case_id TEXT NOT NULL,
 engine_version TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL
);
