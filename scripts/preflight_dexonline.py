"""Read-only schema and licensing preflight for the official DEXonline SQL dump."""
import gzip
import os
import re
from pathlib import Path

TABLES = {"Source", "SourceType", "Definition", "Lexeme", "InflectedForm"}
CREATE = re.compile(r"^CREATE TABLE `([^`]+)`")
COLUMN = re.compile(r"^\s+`([^`]+)`\s+")
INSERT = re.compile(r"^INSERT INTO `([^`]+)`(?:\s*\([^)]*\))?\s+VALUES\s", re.I)

def inspect(path):
    columns = {}
    insert_counts = {name: 0 for name in TABLES}
    current = None
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = CREATE.match(line)
            if match:
                current = match.group(1) if match.group(1) in TABLES else None
                if current:
                    columns[current] = []
                continue
            if current is not None:
                if line.startswith(")"):
                    current = None
                else:
                    column = COLUMN.match(line)
                    if column:
                        columns[current].append(column.group(1))
                continue
            match = INSERT.match(line)
            if match and match.group(1) in TABLES:
                insert_counts[match.group(1)] += 1
    return columns, insert_counts

def main():
    path = Path(os.environ.get("DEX_DUMP", "/tmp/dex-database.sql.gz"))
    if not path.is_file():
        raise SystemExit(f"Archive not found: {path}")
    columns, inserts = inspect(path)
    for name in sorted(TABLES):
        print(f"{name}: columns={columns.get(name, [])}; insert_statements={inserts[name]}")
    missing = TABLES - columns.keys()
    if missing:
        raise SystemExit(f"Missing schemas: {sorted(missing)}")
    source = set(columns["Source"])
    definition = set(columns["Definition"])
    if "canDistribute" not in source:
        raise SystemExit("LICENSE GATE: Source.canDistribute is absent; review actual licensing metadata before importing.")
    if not {"id", "sourceId"}.issubset(definition):
        raise SystemExit("SCHEMA GATE: Definition.id/sourceId missing; review import mapping.")
    if not all(inserts.values()):
        raise SystemExit("DATA GATE: At least one required table has no recognized INSERT statements.")
    print("Preflight passed. Read-only; no database writes.")

if __name__ == "__main__":
    main()
