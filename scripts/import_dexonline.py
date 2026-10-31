"""Conservative DEXonline import gate. Does not load unlicensed content."""
import gzip
import os
import re
from pathlib import Path

TABLES = ("Abbreviation", "Entry", "EntryDefinition", "EntryLexeme", "Fragment",
          "InflectedForm", "Inflection", "Lexeme", "LexemeSource", "Loc",
          "Meaning", "MeaningSource", "Model", "ModelType", "ObjectTag",
          "Relation", "Source", "SourceType", "Tag", "Tree", "TreeEntry",
          "Definition", "DefinitionSimple")

def main():
    path = Path(os.getenv("DEX_DUMP", "/tmp/dex-database.sql.gz"))
    if not path.is_file():
        raise SystemExit("DEX dump not found")
    found = set()
    source_columns = None
    source_rows = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = re.match(r"CREATE TABLE `([^`]+)`", line)
            if match:
                found.add(match.group(1))
            if line.startswith("INSERT INTO `Source`"):
                source_rows += 1
    print("Tables found:", len(found))
    print("Requested tables present:", sorted(set(TABLES) & found))
    print("Missing:", sorted(set(TABLES) - found))
    print("Source insert statements:", source_rows)
    if set(TABLES) - found:
        raise SystemExit("Missing required tables; schema mapping must be reviewed")
    if os.getenv("DRY_RUN", "true").lower() != "true":
        raise SystemExit("Import intentionally blocked: licensing-aware source joins, referential integrity and resumable batching must be implemented and tested before writing production data.")
    print("Dry run successful. No database writes performed.")

if __name__ == "__main__":
    main()
