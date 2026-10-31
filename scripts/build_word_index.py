"""Conservative DEXonline word index builder.

Preview is read-only. Publishing requires explicit independent license approval.
Only lexemes linked to redistributable sources via LexemeSource are eligible.
"""
import gzip
import os
import re
import unicodedata
from collections import Counter
from import_licensed_definitions import values

CREATE = re.compile(r"^CREATE TABLE `([^`]+)`")
COLUMN = re.compile(r"^\s+`([^`]+)`\s+")
INSERT = re.compile(r"^INSERT INTO `([^`]+)` VALUES (.*);$")
TABLES = {"Source", "LexemeSource", "InflectedForm"}

def normalize(raw):
    if not raw:
        return None
    # DEXonline stress apostrophes are not orthographic letters.
    raw = raw.replace("'", "").replace("’", "").replace("ʼ", "")
    raw = raw.translate(str.maketrans({"ă": "a", "â": "a", "î": "i", "ș": "s", "ş": "s", "ț": "t", "ţ": "t",
                                        "Ă": "A", "Â": "A", "Î": "I", "Ș": "S", "Ş": "S", "Ț": "T", "Ţ": "T"}))
    raw = "".join(c for c in unicodedata.normalize("NFD", raw) if unicodedata.category(c) != "Mn").upper()
    return raw if re.fullmatch(r"[A-Z]{2,20}", raw) else None

def scan(path, wanted):
    cols = {}
    current = None
    with gzip.open(path, "rt", encoding="utf-8", errors="strict") as stream:
        for line in stream:
            m = CREATE.match(line)
            if m:
                current = m.group(1) if m.group(1) in wanted else None
                if current:
                    cols[current] = []
                continue
            if current:
                if line.startswith(")"):
                    current = None
                else:
                    c = COLUMN.match(line)
                    if c:
                        cols[current].append(c.group(1))
                continue
            m = INSERT.match(line)
            if not m or m.group(1) not in wanted:
                continue
            table = m.group(1)
            if table not in cols:
                raise RuntimeError(f"Missing CREATE TABLE for {table}")
            for fields in values(m.group(2)):
                if len(fields) != len(cols[table]):
                    raise RuntimeError(f"Invalid column count: {table}")
                yield table, dict(zip(cols[table], fields))

def build(path):
    licensed = set()
    lexemes = set()
    source_columns = None
    for table, row in scan(path, {"Source"}):
        source_columns = row.keys()
        if row.get("canDistribute") == "1":
            licensed.add(str(row["id"]))
    if not licensed or source_columns is None:
        raise RuntimeError("Missing licensed source metadata")
    relations = 0
    for table, row in scan(path, {"LexemeSource"}):
        if "lexemeId" not in row or "sourceId" not in row:
            raise RuntimeError("LexemeSource relation columns not as expected")
        relations += 1
        if str(row["sourceId"]) in licensed:
            lexemes.add(str(row["lexemeId"]))
    if not relations:
        raise RuntimeError("No LexemeSource relationships: fail closed")
    candidates = set()
    stats = Counter()
    for table, row in scan(path, {"InflectedForm"}):
        stats["forms_scanned"] += 1
        if str(row.get("lexemeId")) not in lexemes:
            continue
        stats["licensed_lexeme_forms"] += 1
        word = normalize(row.get("formNoAccent") or row.get("form"))
        if word:
            candidates.add(word)
        else:
            stats["invalid_forms"] += 1
    return candidates, stats, len(lexemes), licensed

def main():
    words, stats, lexemes, sources = build(os.getenv("DEX_DUMP", "/tmp/dex-database.sql.gz"))
    print(f"Licensed source IDs: {sorted(sources)}; linked lexemes: {lexemes}")
    print(f"Scanned: {dict(stats)}; distinct normalized candidates: {len(words)}")
    print(f"ROGI candidate: {'ROGI' in words}")
    if os.getenv("PUBLISH_WORDS", "false").lower() != "true":
        print("PREVIEW ONLY: no database writes")
        return
    if os.getenv("LICENSE_APPROVED") != "true":
        raise SystemExit("Publication blocked: independently review and approve rights to inflected forms first")
    import psycopg
    uri = os.getenv("DATABASE_URL")
    if not uri:
        raise SystemExit("Missing DATABASE_URL")
    batch_size = int(os.getenv("BATCH_SIZE", "500"))
    if not 1 <= batch_size <= 1000:
        raise SystemExit("BATCH_SIZE must be 1..1000")
    # Safe incremental upserts. Never delete existing words.
    with psycopg.connect(uri, connect_timeout=30) as db:
        ordered = sorted(words)
        for start in range(0, len(ordered), batch_size):
            batch = ordered[start:start + batch_size]
            with db.transaction():
                with db.cursor() as cur:
                    cur.executemany("insert into public.dictionary_words(word,source,verified) values (%s,'dexonline',true) on conflict (word) do update set verified=true, updated_at=now()", [(w,) for w in batch])
            if (start // batch_size) % 100 == 0:
                print(f"Published {min(start+batch_size,len(ordered))}/{len(ordered)}")
        with db.cursor() as cur:
            cur.execute("select count(*) from public.dictionary_words where source='dexonline' and verified=true")
            print("Verified indexed words:", cur.fetchone()[0])
            cur.execute("select word from public.dictionary_words where word='ROGI'")
            print("ROGI indexed:", cur.fetchone() is not None)

if __name__ == "__main__":
    main()
