"""Streaming, resumable, source-gated DEXonline import.

Only imports source metadata and definitions explicitly marked redistributable.
Other tables require a reviewed relation-level licensing strategy.
"""
import gzip
import os
import re
import sys
import json

import psycopg
from psycopg.types.json import Jsonb

TABLES = ("Source", "SourceType", "Definition")
INSERT = re.compile(r"^INSERT INTO `([^`]+)` VALUES (.*);$")
CREATE = re.compile(r"^CREATE TABLE `([^`]+)`")
COLUMN = re.compile(r"^  `([^`]+)`")

def values(sql):
    row, field, quoted, escaped, active = [], [], False, False, False
    for char in sql:
        if not active:
            if char == "(":
                row, field, active = [], [], True
            continue
        if quoted:
            if escaped:
                field.append({"n": "\n", "r": "\r", "t": "\t", "0": "\x00"}.get(char, char))
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                quoted = False
            else:
                field.append(char)
        elif char == "'":
            quoted = True
        elif char == ",":
            raw = "".join(field).strip()
            row.append(None if raw == "NULL" else raw)
            field = []
        elif char == ")":
            raw = "".join(field).strip()
            row.append(None if raw == "NULL" else raw)
            yield row
            active = False
        else:
            field.append(char)

def main():
    uri = os.environ.get("DATABASE_URL")
    if not uri:
        raise SystemExit("DATABASE_URL GitHub Actions secret is required")
    archive = os.environ.get("DEX_DUMP", "/tmp/dex-database.sql.gz")
    cols, permitted = {}, set()
    counts = {name: 0 for name in TABLES}
    with psycopg.connect(uri, connect_timeout=30) as db:
        with db.cursor() as cur:
            cur.execute("select count(*) from dexonline.import_manifest")
            print("Prepared tables:", cur.fetchone()[0])
        db.commit()
        # The official dump is alphabetical: Definition occurs before Source.\n        # Pass 1 imports Source and SourceType, pass 2 imports licensed Definition.
        with gzip.open(archive, "rt", encoding="utf-8", errors="replace") as stream:
            for line in stream:
                match = CREATE.match(line)
                if match and match.group(1) in phase:
                    table = match.group(1)
                    columns = []
                    for schema_line in stream:
                        if schema_line.startswith(") ENGINE"):
                            break
                        column = COLUMN.match(schema_line)
                        if column:
                            columns.append(column.group(1))
                    cols[table] = columns
                    continue
                match = INSERT.match(line)
                if not match or match.group(1) not in phase:
                    continue
                table = match.group(1)
                if table not in cols:
                    raise RuntimeError(f"Missing schema for {table}")
                batch = []
                for fields in values(match.group(2)):
                    if len(fields) != len(cols[table]):
                        raise RuntimeError(f"Malformed row in {table}")
                    obj = dict(zip(cols[table], fields))
                    if table == "Source":
                        if str(obj.get("canDistribute")) == "1":
                            permitted.add(str(obj["id"]))
                        # Metadata of nonredistributable sources is retained only for audit.
                    if table == "Definition" and str(obj.get("sourceId")) not in permitted:
                        continue
                    batch.append((int(obj["id"]), Jsonb(obj)))
                    if len(batch) >= 500:
                        write(db, table, batch)
                        counts[table] += len(batch)
                        batch.clear()
                if batch:
                    write(db, table, batch)
                    counts[table] += len(batch)
        with db.cursor() as cur:
            for table, count in counts.items():
                cur.execute('update dexonline.import_manifest set imported_rows=(select count(*) from dexonline."' + table + '"), status=%s, updated_at=now() where source_table=%s', ("partial_licensed_import", table))
        db.commit()
    print(json.dumps({"processed_rows": counts, "redistributable_source_ids": sorted(permitted)}))
    print("WARNING: This imports only Source, SourceType and licensed Definition. Remaining 20 tables and game index are NOT imported.")

def write(db, table, batch):
    with db.cursor() as cur:
        cur.executemany('insert into dexonline."' + table + '" (id,payload) values (%s,%s) on conflict (id) do update set payload=excluded.payload', batch)
    db.commit()

if __name__ == "__main__":
    main()
