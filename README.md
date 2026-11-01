# DEXonline adapter for Mini Cuvinte

This repository contains an **unofficial Python HTML adapter**, not an official DEXonline API and not yet a bulk dictionary importer.

- [How to change DEXonline URLs/selectors](docs/DEXONLINE_SOURCE.md)
- [Planned versioned import into Supabase](docs/IMPORT_PIPELINE.md)
- [Game repository](https://github.com/mini-cuvinte/game)
- [Clean deployment instructions](https://github.com/mini-cuvinte/game/blob/main/docs/DEPLOY_FROM_ZERO.md)

Configurable environment variables: `DEXONLINE_BASE_URL`, `DEXONLINE_TIMEOUT`, `DEXONLINE_DEFINITION_SELECTOR`. See the source-maintenance guide.

**License note:** verify permission to retrieve, store, use and redistribute DEXonline-derived dictionary content before running imports. No full dictionary dataset is committed here.

---

## Original package documentation

# Dexonline.ro API

A simple API that queries dexonline.ro, it returns the definitions of the words.
>This is not an official API
#
What is dexonline - [info](https://wiki.dexonline.ro/wiki/Informații)
#

How to install, using pip install?

>pip install dexonlineBK

#

### Functionality
The first thing we need to do is import the library
```python
from dexonlineBK import dexonlineBK as DO
```
The first, and most important, function is getWordDefinition()
This function returns the list of lists
```python
definitions = DO.getWordDefinition("neexplicabil")

for defs in definitions:
	print(defs[0])
	print(defs[1] + "\n")
```
Output:
```
NEEXPLICÁBIL
adj. v. inexplicabil.

NEEXPLICABIL
adj. inexplicabil, neînțeles. (Un fapt ~.)

Neexplicabil
≠ explicabil
```
For more printing comfort I have the toString() function
```python
DO.toString(definitions)
```
Output:
```
WORD: NEEXPLICÁBIL
DEFINITION: adj. v. inexplicabil.

WORD: NEEXPLICABIL
DEFINITION: adj. inexplicabil, neînțeles. (Un fapt ~.)

WORD: Neexplicabil
DEFINITION: ≠ explicabil
```
getWordOfTheDay() function, returns the list with the word and its definition
toString() also works with this function
```python
DO.toString(DO.getWordOfTheDay())
```
Output:
```python
WORD: ARÉIC, -Ă,
DEFINITION: areici, -ce, adj. (Geol.; despre regiuni, soluri) Lipsit de apă, uscat, arid. [Pr.: -re-ic] – Din fr. aréique.
```
getWordOfTheMonth() function, returns the list with the word and its definition
toString() also works with this function
```python
DO.toString(DO.getWordOfTheMonth())
```
Output:
```python
WORD: ntur
DEFINITION: i [At: ALR II, 5752/791 / E: fo] (Reg) Onomatopee care imită trilurile turturicii.
```
reallyExist() function, returns boolean.
dexonline.ro have list of words in romanina.
And here you check if this word exists in Romanian.
```python
print(DO.reallyExist('mama'))
```
Output:
```python
True
```
randomWord() function, returns random word.
dexonline.ro have a page with 100 random words.
```python
print(DO.randomWord())
```
Output:
```python
desfălura
```
```python
DO.toString(DO.getWordDefinition(DO.randomWord()))
```
Output:
```python
WORD: desfălura
DEFINITION: vr [At: DUMITRAȘCU, STR. 13 / V: ~lău~, ~fău~ / Pzi: ~rez / E: nct] (Olt) 1 A se descheia la haină. 2 (Pex) A se dezbrăca de haină, rămânând doar în cămașă.

WORD: desfălăura
DEFINITION: v vz desfălura

WORD: desfăura
DEFINITION: v vz desfălura
```
#
>The API is still being tested


## Mini Cuvinte integration and maintenance

This repository is a **Python HTML client for DEXonline**, not an official API and **not yet a bulk Supabase importer**. Mini Cuvinte stores its own dictionary locally; game moves never need to call this client.

### Install for development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install requests beautifulsoup4 html5lib
python -c "from dexonlineBK import dexonlineBK as dex; print(dex.getWordDefinition('casa'))"
```

The legacy `setup.py` has outdated dependency metadata; the commands above install the required libraries directly.

### Change the source if DEXonline changes

| Setting | Default | What it changes |
|---|---|---|
| `DEXONLINE_BASE_URL` | `https://dexonline.ro` | Source host, not URL paths |
| `DEXONLINE_DEFINITION_SELECTOR` | `span.def` | CSS selector used for definition blocks |
| `DEXONLINE_TIMEOUT` | `15` | HTTP timeout in seconds |

If the page URL structure changes, update `dexonlineBK/dexonlineBK.py` in the functions `getWordDefinition`, `getParadigms`, `getWordOfTheDay`, `getWordOfTheMonth` and `randomWord`. If the HTML changes, inspect `getTags` and the functions that parse definition nodes. Verify results with a small, permitted sample before release.

Upstream references: [DEXonline website](https://dexonline.ro/), [DEXonline source code](https://github.com/dexonline/dexonline), [DEXonline wiki](https://wiki.dexonline.ro/). Respect source terms, attribution and dataset licensing. Do not assume the right to scrape or redistribute bulk dictionary content.

### Planned ETL pipeline

1. Retrieve permitted word data into a versioned staging set.
2. Normalize Romanian characters, deduplicate and validate counts.
3. Record source URL, license, date, checksum and importer version.
4. Populate Mini Cuvinte `dictionary_private` staging/version tables in Supabase.
5. Approve and activate the new dictionary version; retain the previous version for rollback.

**Not implemented yet:** bulk import, scheduled synchronization and version publishing automation. The current Python client alone cannot populate the entire game dictionary. For the broader architecture see [game/docs/DEXONLINE.md](https://github.com/mini-cuvinte/game/blob/main/docs/DEXONLINE.md).
