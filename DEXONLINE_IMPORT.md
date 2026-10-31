# DEXonline import — Mini Cuvinte

## Authoritative sources
- Official SQL archive: https://dexonline.ro/static/download/dex-database.sql.gz
- Official installation guide: https://wiki.dexonline.ro/wiki/Instruc%C8%9Biuni_de_instalare
- DEXonline licensing and permitted redistribution: https://wiki.dexonline.ro/wiki/Licen%C8%9Be
- DEXonline project: https://dexonline.ro/

## Running
Go to GitHub Actions > DEXonline import (manual) > Run workflow.
Select branch `modernize/python-fastapi`. Start with `dry_run=true`.
This workflow currently **only audits** the official archive; it does **not** import data.
`dry_run=false` deliberately fails safely rather than importing unfiltered data.

## Security
Store the PostgreSQL Session Pooler URI as repository secret `DATABASE_URL` only
when the import implementation is audited and ready. Never commit credentials.
Do not grant public read access to raw staging tables.

## Planned 23 tables
Abbreviation, Entry, EntryDefinition, EntryLexeme, Fragment, InflectedForm,
Inflection, Lexeme, LexemeSource, Loc, Meaning, MeaningSource, Model, ModelType,
ObjectTag, Relation, Source, SourceType, Tag, Tree, TreeEntry, Definition,
DefinitionSimple.

## Before enabling import
- Verify schema columns and keys from the downloaded version.
- Build source-level licensing filters; preserve attribution and license details.
- Verify foreign-key closure for permitted records.
- Import in bounded batches with checkpoints and per-table row counts.
- Check available Supabase storage and index sizes.
- Validate game dictionary policy (inflections, abbreviations, proper names).
- Confirm examples including ROGI; run reconciliation SQL and only then publish.
