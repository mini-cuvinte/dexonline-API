# Dictionary release pipeline for Mini Cuvinte

The `dexonlineBK` package is a lookup/scraping adapter, **not** a bulk import tool. The game's live dictionary is stored in Supabase PostgreSQL and is not queried from DEXonline during turns.

Proposed release flow:

1. Obtain an authorized dataset or permitted source export. Confirm attribution, redistribution and usage rights before ingestion.
2. Normalize and deduplicate Romanian words, preserving the appropriate diacritics and accepted inflections.
3. Create a candidate record in `dictionary_private.versions` with `status='building'`, `license_approved=false` until approval, source metadata, count and checksum.
4. Load into `dictionary_private.entries` in batches with retry/checkpoint support. Do not place the full dictionary in public GitHub.
5. Compare actual counts, checksums and samples; test accepted and rejected words and any moderation overrides.
6. Set license approval only after verified authorization. Publish atomically using `dictionary_private.publish_version` after reviewing its current preconditions.
7. Keep the previously active version for rollback. Monitor errors and publish only after game smoke tests.

The existing database also contains a `dexonline` staging schema with 24 tables. That is **not required** for a clean game install; if the future ETL depends on it, version its schema in this repository separately.

For now, the import runner and dataset manifest are **not implemented**. Do not claim that a full DEXonline synchronization is available.

See [source maintenance](DEXONLINE_SOURCE.md) and [game deployment](https://github.com/mini-cuvinte/game/blob/main/docs/DEPLOY_FROM_ZERO.md).
