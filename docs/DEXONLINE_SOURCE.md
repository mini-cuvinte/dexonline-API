# DEXonline source adapter

This is a **third-party, unofficial HTML adapter**, not an official DEXonline API or a bulk lexicon feed.

## Configuration

- `DEXONLINE_BASE_URL` — defaults to `https://dexonline.ro`.
- `DEXONLINE_TIMEOUT` — HTTP timeout in seconds; defaults to `15`.
- `DEXONLINE_DEFINITION_SELECTOR` — CSS selector for definition elements; defaults to `span.def`.

The Python implementation is in `dexonlineBK/dexonlineBK.py`. It builds these paths relative to `DEXONLINE_BASE_URL`:

- `/definitie/{url-encoded-word}/expandat`
- `/definitie/{url-encoded-word}/expandat/paradigma`
- `/cuvantul-zilei`
- `/cuvantul-lunii`
- `/cuvinte-aleatorii`

Other HTML selectors, such as `ul.commaList` and `div.col-md-12.main-content`, are still embedded in the adapter. Changing only the definition selector may not fix all methods.

## If DEXonline changes its website

1. Check the DEXonline documentation, terms, robots/access restrictions, and licensing. Prefer an authorized official export/API over scraping.
2. Update the environment variable `DEXONLINE_BASE_URL` if the host changes.
3. If definition HTML changes, update `DEXONLINE_DEFINITION_SELECTOR` first; for other layouts update `dexonlineBK/dexonlineBK.py` in this repository.
4. Run targeted tests against permitted sample words, including Romanian diacritics, missing words and inflected forms.
5. Review results and release a tagged version. Do not automatically publish extracted dictionary content to a public repository.
6. Only then run the separate Mini Cuvinte dictionary import job and publish a new dictionary version after validation.

## Known limitations

- `reallyExist()` currently reads `loc-flexiuni-6.0.txt` relative to the working directory, **not** from the remote API; it is unsuitable for a reliable hosted dictionary without packaging that file or replacing the implementation.
- `getWordDefinition()` relies on DEXonline's HTML structure and has weak error handling.
- The adapter is not a complete, versioned bulk-import pipeline. A proper import job with licensing, checkpoints, validation, and publish/rollback is still needed.

Related repository: https://github.com/mini-cuvinte/game.
