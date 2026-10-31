"""Read-only sample of the official DEXonline dump; never connects to Supabase."""
import gzip
import json
import os
import re
from pathlib import Path
from import_licensed_definitions import values

CREATE = re.compile(r"^CREATE TABLE `([^`]+)`")
COLUMN = re.compile(r"^\s+`([^`]+)`\s+")
INSERT = re.compile(r"^INSERT INTO `([^`]+)` VALUES (.*);$")
TABLES = ("Source", "Definition", "InflectedForm", "Lexeme")

def sample(path, limit=100):
    columns = {}
    samples = {table: [] for table in TABLES}
    with gzip.open(path, "rt", encoding="utf-8", errors="strict") as stream:
        current = None
        for line in stream:
            m = CREATE.match(line)
            if m:
                current = m.group(1) if m.group(1) in TABLES else None
                if current:
                    columns[current] = []
                continue
            if current:
                if line.startswith(")"):
                    current = None
                else:
                    col = COLUMN.match(line)
                    if col:
                        columns[current].append(col.group(1))
                continue
            m = INSERT.match(line)
            if not m or m.group(1) not in TABLES:
                continue
            table = m.group(1)
            if table not in columns:
                raise ValueError(f"Missing CREATE TABLE for {table}")
            for fields in values(m.group(2)):
                if len(fields) != len(columns[table]):
                    raise ValueError(f"Invalid column count in {table}: {len(fields)} != {len(columns[table])}")
                if len(samples[table]) < limit:
                    samples[table].append(dict(zip(columns[table], fields)))
            # Continue scanning other tables but don't retain excess rows.
    return samples

def main():
    limit = int(os.getenv("SAMPLE_LIMIT", "100"))
    if not 1 <= limit <= 100:
        raise SystemExit("SAMPLE_LIMIT must be between 1 and 100")
    samples = sample(Path(os.getenv("DEX_DUMP", "/tmp/dex-database.sql.gz")), limit)
    for table, rows in samples.items():
        print(f"{table}: parsed={len(rows)}")
        if not rows:
            raise SystemExit(f"No sample rows in {table}")
    sources = samples["Source"]
    allowed = [s for s in sources if s.get("canDistribute") == "1"]
    print("Source license flags:", json.dumps({str(s.get("id")): s.get("canDistribute") for s in sources}, ensure_ascii=False))
    print("Redistributable sources in sample:", len(allowed))
    print("ROGI in first InflectedForm sample:", any(str(x.get("formNoAccent", "")).upper() == "ROGI" for x in samples["InflectedForm"]))
    print("Read-only sample completed; zero database writes.")

if __name__ == "__main__":
    main()
