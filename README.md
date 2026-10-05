# Automated Data Cleaning Tool

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/cleaning/main.py`](src/cleaning/main.py) | HTTP handlers: `GET /healthz`, `POST /clean` |
| [`src/cleaning/ops.py`](src/cleaning/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/cleaning/clean.py`](src/cleaning/clean.py) | Functions: `snake`, `coerce`, `iso_date`, `median`, `quartiles`, `clean` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/cleaning/__init__.py`](src/cleaning/__init__.py) | Implementation or supporting configuration |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_clean.py`](tests/test_clean.py) | Executable checks and regression examples |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn cleaning.main:app --reload
```

<!-- project-guide:end -->

Level: 1 — Python fundamentals

Skills: Python, tabular data, type coercion, outlier detection, a written change report

Send rows as JSON objects. The tool cleans a copy and returns the cleaned rows with a report of every kind of change. The input is never modified.

Steps, in order:

1. Rename columns to snake case (`First Name` becomes `first_name`).
2. Strip whitespace, and treat an empty string as missing.
3. Turn numeric strings into numbers (`"1,250"` becomes `1250`).
4. Normalize the columns listed in `date_columns` to ISO dates. A value in an unknown format is refused rather than guessed.
5. Drop exact duplicate rows.
6. Fill missing numbers with `median` (default), `mean`, or `zero`, or `drop` the row, or leave them with `none`.
7. Flag outliers outside 1.5 times the interquartile range. Outliers are reported, not removed.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn cleaning.main:app --reload
```

```bash
curl -s -X POST localhost:8000/clean -H 'content-type: application/json' \
  -d '{"rows":[{"Name":" ada ","Score":"10"},{"Name":"bob","Score":""}],"fill":"median"}'
```

The report has `renamed`, `stripped`, `coerced`, `dates`, `dropped_duplicates`, `filled`, `dropped_missing`, and `outliers` with the row, column, value, and the bounds it fell outside.

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.
