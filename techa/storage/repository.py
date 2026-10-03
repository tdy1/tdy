from __future__ import annotations
import sqlite3
from pathlib import Path

class SQLiteStore:
    def __init__(self,path:str|Path) -> None:
        self.db=sqlite3.connect(str(path)); self.db.execute("PRAGMA foreign_keys=ON")
    def initialize(self,schema_path:str|Path)->None:
        self.db.executescript(Path(schema_path).read_text(encoding="utf-8")); self.db.commit()
    def close(self)->None: self.db.close()
