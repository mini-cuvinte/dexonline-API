"""Bounded, transactional DEXonline import smoke test (100 licensed definitions max).

No public dictionary changes. No writes to non-redistributable sources.
"""
import gzip
import os
import re
import psycopg
from psycopg.types.json import Jsonb
from import_licensed_definitions import values

CREATE = re.compile(r"^CREATE TABLE `([^`]+)`")
COLUMN = re.compile(r"^\s+`([^`]+)`\s+")
INSERT = re.compile(r"^INSERT INTO `([^`]+)` VALUES (.*);$")
TABLES = ("Source", "SourceType", "Definition")

def scan(archive, targets):
    columns = {}
    with gzip.open(archive, "rt", encoding="utf-8", errors="strict") as stream:
        current = None
        for line in stream:
            m = CREATE.match(line)
            if m:
                current = m.group(1) if m.group(1) in targets else None
                if current:
                    columns[current] = []
                continue
            if current:
                if line.startswith(")"):
                    current = None
                else:
                    c = COLUMN.match(line)
                    if c:
                        columns[current].append(c.group(1))
                continue
            m = INSERT.match(line)
            if not m or m.group(1) not in targets:
                continue
            table = m.group(1)
            if table not in columns:
                raise ValueError(f"No schema for {table}")
            for fields in values(m.group(2)):
                if len(fields) != len(columns[table]):
                    raise ValueError(f"Column mismatch in {table}")
                yield table, dict(zip(columns[table], fields))

def main():
    uri = os.environ.get("DATABASE_URL")
    if not uri:
        raise SystemExit("DATABASE_URL secret missing")
    archive = os.environ.get("DEX_DUMP", "/tmp/dex-database.sql.gz")
    limit = int(os.environ.get("SMOKE_LIMIT", "100"))
    if not 1 <= limit <= 100:
        raise SystemExit("SMOKE_LIMIT must be 1..100")
    sources = {}
    source_types = {}
    for table, row in scan(archive, {"Source", "SourceType"}):
        if table == "Source" and row.get("canDistribute") == "1":
            sources[str(row["id"])] = row
        elif table == "SourceType":
            source_types[str(row["id"])] = row
    if not sources:
        raise SystemExit("No explicitly redistributable sources")
    definitions = []
    for table, row in scan(archive, {"Definition"}):
        if str(row.get("sourceId")) in sources:
            definitions.append(row)
            if len(definitions) == limit:
                break
    if not definitions:
        raise SystemExit("No eligible definitions found")
    with psycopg.connect(uri, connect_timeout=30) as db:
        with db.transaction():
            with db.cursor() as cur:
                for table, rows in (("SourceType", source_types.values()), ("Source", sources.values()), ("Definition", definitions)):
                    data = [(int(row["id"]), Jsonb(row)) for row in rows]
                    cur.executemany(f'insert into dexonline."{table}" (id,payload) values (%s,%s) on conflict (id) do update set payload=excluded.payload', data)
                cur.execute('select count(*) from dexonline."Definition" where payload->>\'sourceId\' = any(%s)', (list(sources),))
                verified = cur.fetchone()[0]
                if verified < len(definitions):
                    raise RuntimeError("Database verification failed; transaction will roll back")
        print(f"Committed {len(definitions)} eligible definitions, {len(sources)} licensed sources, {len(source_types)} source types; verified count={verified}")
        print("public.dictionary_words untouched; no flexions imported")

if __name__ == "__main__":
    main()
