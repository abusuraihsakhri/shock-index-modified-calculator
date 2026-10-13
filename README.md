# Shock Index Modified Calculator

An educational and research-oriented calculator for common hemodynamic indices. The static browser interface works without a server; a standard-library Python implementation, CLI, CSV batch processor and optional FastAPI service are included.

## Calculations

| Measure | Formula | Required values |
| --- | --- | --- |
| Shock Index (SI) | HR / SBP | Heart rate (bpm), systolic BP (mmHg) |
| Modified Shock Index (MSI) | HR / MAP | HR, SBP, diastolic BP (mmHg) |
| Mean arterial pressure (MAP) | DBP + (SBP - DBP) / 3 | SBP, DBP |
| Age Shock Index (Age-SI) | Age (years) × SI | HR, SBP, age |
| Reverse SI | SBP / HR | HR, SBP |

**Age-SI is age multiplied by SI**, as originally studied by Zarzaur et al.; it is not SI divided by normalized age. The Python module also contains exploratory pediatric ranges, which are not validated stand-alone triage rules.

**Clinical limitation:** SI and MSI do not diagnose shock or determine treatment. Cutoffs vary by setting and population, and values cannot establish an individual's mortality risk. MSI below 0.7 or above 1.3 has been associated with adverse outcomes in observational emergency-department cohorts; these are research findings rather than management thresholds.

References:
- Zarzaur et al. *J Surg Res*. 2008. [PMID 18498875](https://pubmed.ncbi.nlm.nih.gov/18498875/).
- Liu et al. *World J Emerg Med*. 2012. [PMCID PMC4129788](https://pmc.ncbi.nlm.nih.gov/articles/4129788/).
- Al Jalbout et al. *Arch Acad Emerg Med*. 2023. [PMCID PMC10197905](https://pmc.ncbi.nlm.nih.gov/articles/PMC10197905/).

## Browser application

Open `web/index.html` in a recent browser or serve the `web/` directory as static files. Enter heart rate, systolic pressure, optional diastolic pressure and age. The result panel shows all calculable indices and explanatory context.

For batch processing, select a CSV with headers `hr` (or `heart_rate`) and `sbp`; `dbp` and `age` are optional. Quoted CSV cells are supported, invalid rows are marked and exported cells are escaped against spreadsheet formula execution. Maximum: 2 MB and 2,000 records.

The browser interface uses plain HTML, CSS and JavaScript without third-party scripts, cookies, analytics, accounts or network requests for calculations. Selected CSV files are processed locally; they are **not uploaded to the API**. Avoid placing identifiable patient information in exported or shared files.

## Python and CLI

Python 3.10+ is supported. Core functions in `shock_index.py` use only the standard library.

```bash
python cli.py single --hr 80 --sbp 120 --dbp 80 --age 50
python cli.py batch -i sample.csv -o results.csv
python -m pytest -q
```

Python CSV processing preserves original columns, annotates invalid rows and protects exported cells from spreadsheet formula injection. Nonfinite numeric values raise errors; DBP cannot exceed SBP.

## Optional HTTP service

```bash
python -m pip install -r requirements.txt
uvicorn agents.api:app --reload
```

Open `http://127.0.0.1:8000/` for the same browser UI and `http://127.0.0.1:8000/docs` for API documentation. `POST /api/calculate` accepts JSON such as:

```json
{"hr": 80, "sbp": 120, "dbp": 80, "age": 50}
```

Existing generic supervisor endpoints (`/api/audit`, `/api/chat`, `/api/audit/logs`) and CLI audit/chat commands are retained as **demonstration utilities**, not validated clinical agents. Their mock provider does not call a real LLM. The regex identifier guard is best-effort and **does not ensure HIPAA de-identification**. The HMAC audit chain is held in process memory, not a persistent clinical audit system.

Docker:

```bash
docker build -t shock-index-modified-calculator .
docker run --rm -p 8000:8000 -e AUDIT_SECRET_KEY=replace-with-long-random-secret shock-index-modified-calculator
```

Set a unique strong `AUDIT_SECRET_KEY` for stable local signatures across runs; logs are not persisted between restarts.

## Development and deployment

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --check web/app.js
node --test tests/web.test.cjs
```

GitHub Actions checks Python 3.10–3.12 and Node 22. The Pages workflow publishes the static `web/` directory on the production branch once GitHub Pages uses the GitHub Actions source. No Pyodide or backend Python runtime is needed for this arithmetic-only browser app.

## License

[MIT](LICENSE).
