"""Read-only audit of DEXonline provenance paths and the ROGI lexeme."""
import os
from collections import Counter, defaultdict
from build_word_index import scan

TABLES = {"Source", "Lexeme", "LexemeSource", "EntryLexeme", "EntryDefinition", "Definition", "InflectedForm"}
TARGET = os.getenv("TARGET_WORD", "ROGI").upper()
LIMIT = 12

def main():
    path = os.getenv("DEX_DUMP", "/tmp/dex-database.sql.gz")
    columns, counts = {}, Counter()
    licensed, lexeme_ids, entry_ids, definition_ids = set(), set(), set(), set()
    target_forms = []
    # First pass: locate target and inspect each relation's actual columns.
    for table, row in scan(path, TABLES):
        counts[table] += 1
        if table not in columns:
            columns[table] = list(row)
        if table == "Source" and row.get("canDistribute") == "1":
            licensed.add(str(row["id"]))
        if table == "InflectedForm" and str(row.get("formNoAccent", "")).upper() == TARGET:
            lexeme_ids.add(str(row["lexemeId"]))
            if len(target_forms) < LIMIT:
                target_forms.append({k: row.get(k) for k in ("id", "form", "lexemeId", "inflectionId", "recommended")})
    print("SCHEMA:", columns)
    print("ROW_COUNTS:", dict(counts))
    print("LICENSED_SOURCE_IDS:", sorted(licensed))
    print("TARGET_FORMS:", target_forms)
    print("TARGET_LEXEME_IDS:", sorted(lexeme_ids))
    if not lexeme_ids:
        raise SystemExit("Target lexeme not found; no writes performed")
    # Second pass: traverse relations without assuming their semantic validity.
    direct_sources, linked_entries, lexeme_details = [], [], []
    for table, row in scan(path, {"Lexeme", "LexemeSource", "EntryLexeme"}):
        if table == "Lexeme" and str(row.get("id")) in lexeme_ids:
            lexeme_details.append({k: row.get(k) for k in ("id", "form", "formNoAccent", "modelType", "modelNumber")})
        if table == "LexemeSource" and str(row.get("lexemeId")) in lexeme_ids:
            direct_sources.append(row)
        if table == "EntryLexeme" and str(row.get("lexemeId")) in lexeme_ids:
            linked_entries.append(row)
            if row.get("entryId") is not None:
                entry_ids.add(str(row["entryId"]))
    print("LEXEMES:", lexeme_details[:LIMIT])
    print("DIRECT_LEXEME_SOURCES:", direct_sources[:LIMIT], "total:", len(direct_sources))
    print("ENTRY_LEXEME_LINKS:", linked_entries[:LIMIT], "total:", len(linked_entries))
    # Third pass: entry-to-definition provenance.
    entry_definitions = []
    for table, row in scan(path, {"EntryDefinition"}):
        if str(row.get("entryId")) in entry_ids:
            entry_definitions.append(row)
            if row.get("definitionId") is not None:
                definition_ids.add(str(row["definitionId"]))
    print("ENTRY_DEFINITION_LINKS:", entry_definitions[:LIMIT], "total:", len(entry_definitions))
    source_counts = Counter()
    target_definitions = []
    for table, row in scan(path, {"Definition"}):
        if str(row.get("id")) in definition_ids:
            source = str(row.get("sourceId"))
            source_counts[source] += 1
            if len(target_definitions) < LIMIT:
                target_definitions.append({"id": row.get("id"), "sourceId": source, "redistributable_source": source in licensed})
    print("DEFINITION_SOURCE_COUNTS:", dict(source_counts))
    print("DEFINITION_SAMPLES:", target_definitions)
    print("READ ONLY. Source-level canDistribute is not proof of inflection-data redistribution rights.")

if __name__ == "__main__":
    main()
