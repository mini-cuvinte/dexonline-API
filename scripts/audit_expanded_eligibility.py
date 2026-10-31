"""Audit expanded word provenance; never grants publication rights.

Paths: direct LexemeSource and EntryLexeme -> EntryDefinition -> Definition.
A matching redistributable definition is evidence only, not a license for
the derived InflectedForm dataset.
"""
import os
import time
from collections import Counter, defaultdict
from build_word_index import scan, normalize

def log(message):
    print(message, flush=True)

def main():
    path = os.getenv("DEX_DUMP", "/tmp/dex-database.sql.gz")
    started = time.monotonic()
    licensed = set()
    for _, row in scan(path, {"Source"}):
        if row.get("canDistribute") == "1":
            licensed.add(str(row["id"]))
    if not licensed:
        raise RuntimeError("No redistributable source flags found")
    direct = set()
    for _, row in scan(path, {"LexemeSource"}):
        if str(row.get("sourceId")) in licensed:
            direct.add(str(row["lexemeId"]))
    log(f"[1/5] licensed sources={sorted(licensed)}, direct lexemes={len(direct)}, elapsed={time.monotonic()-started:.1f}s")
    # Store only links needed for provenance; do not store definitions or their text.
    entries_by_lexeme = defaultdict(set)
    for _, row in scan(path, {"EntryLexeme"}):
        entries_by_lexeme[str(row["lexemeId"])].add(str(row["entryId"]))
    entry_definitions = defaultdict(set)
    for _, row in scan(path, {"EntryDefinition"}):
        entry_definitions[str(row["definitionId"])].add(str(row["entryId"]))
    log(f"[2/5] entry links={len(entries_by_lexeme)}, definition links={len(entry_definitions)}, elapsed={time.monotonic()-started:.1f}s")
    licensed_entries = set()
    for _, row in scan(path, {"Definition"}):
        if str(row.get("sourceId")) in licensed:
            licensed_entries.update(entry_definitions.get(str(row["id"]), ()))
    del entry_definitions
    indirect = {lexeme for lexeme, entries in entries_by_lexeme.items() if not entries.isdisjoint(licensed_entries)}
    del entries_by_lexeme
    log(f"[3/5] entries with licensed definitions={len(licensed_entries)}, indirect lexemes={len(indirect)}, elapsed={time.monotonic()-started:.1f}s")
    counters = Counter()
    sets = {"direct": set(), "indirect": set(), "union": set()}
    for _, row in scan(path, {"InflectedForm"}):
        counters["forms_scanned"] += 1
        if row.get("recommended") != "1":
            counters["not_recommended"] += 1
            continue
        word = normalize(row.get("formNoAccent") or row.get("form"))
        if not word:
            counters["invalid_word"] += 1
            continue
        lexeme = str(row.get("lexemeId"))
        if lexeme in direct:
            sets["direct"].add(word)
        if lexeme in indirect:
            sets["indirect"].add(word)
        if lexeme in direct or lexeme in indirect:
            sets["union"].add(word)
        if counters["forms_scanned"] % 500000 == 0:
            log(f"[4/5] scanned={counters['forms_scanned']:,}, elapsed={time.monotonic()-started:.1f}s")
    log(f"[5/5] counts={dict(counters)}, distinct_direct={len(sets['direct'])}, distinct_indirect={len(sets['indirect'])}, distinct_union={len(sets['union'])}")
    log(f"ROGI direct={'ROGI' in sets['direct']}, indirect={'ROGI' in sets['indirect']}, union={'ROGI' in sets['union']}")
    log("AUDIT ONLY: neither direct nor indirect provenance grants rights to redistribute flexions. No database writes.")
    log(f"Elapsed={time.monotonic()-started:.1f}s")

if __name__ == "__main__":
    main()
