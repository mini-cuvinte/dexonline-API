"""Read-only full-dump scan for game-word candidates; does not publish or import."""
import gzip
import os
import re
import unicodedata
from collections import Counter
from import_licensed_definitions import values

CREATE = re.compile(r"^CREATE TABLE `([^`]+)`")
COLUMN = re.compile(r"^\s+`([^`]+)`\s+")
INSERT = re.compile(r"^INSERT INTO `(InflectedForm|Lexeme)` VALUES (.*);$")
TARGET = os.getenv("TARGET_WORD", "ROGI").upper()

def normalize(word):
    return "".join(c for c in unicodedata.normalize("NFD", word) if unicodedata.category(c) != "Mn").upper()

def main():
    archive = os.getenv("DEX_DUMP", "/tmp/dex-database.sql.gz")
    columns = {}
    current = None
    stats = Counter()
    matches = []
    with gzip.open(archive, "rt", encoding="utf-8", errors="strict") as stream:
        for line in stream:
            m = CREATE.match(line)
            if m:
                current = m.group(1) if m.group(1) in ("InflectedForm", "Lexeme") else None
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
            if not m:
                continue
            table = m.group(1)
            names = columns.get(table)
            if not names or "formNoAccent" not in names:
                raise RuntimeError(f"Missing expected columns for {table}")
            idx = names.index("formNoAccent")
            for fields in values(m.group(2)):
                if len(fields) != len(names):
                    raise RuntimeError(f"Column count mismatch in {table}")
                stats[table] += 1
                form = fields[idx]
                if form and normalize(form) == TARGET:
                    matches.append({key: fields[names.index(key)] for key in ("id", "form", "formNoAccent") if key in names} | {"table": table, "lexemeId": fields[names.index("lexemeId")] if "lexemeId" in names else None})
    print("Rows scanned:", dict(stats))
    print(f"Matches for {TARGET}: {len(matches)}")
    for match in matches[:20]:
        print(match)
    print("READ ONLY. No words imported or published.")

if __name__ == "__main__":
    main()
