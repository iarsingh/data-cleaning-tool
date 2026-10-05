# data-cleaning-tool — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does data-cleaning-tool address, and what can you demonstrate?

Send rows as JSON objects. The tool cleans a copy and returns the cleaned rows with a report of every kind of change. The input is never modified.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/cleaning/main.py`](src/cleaning/main.py): Implementation or supporting configuration.
- [`src/cleaning/ops.py`](src/cleaning/ops.py): Implementation or supporting configuration.
- [`src/cleaning/clean.py`](src/cleaning/clean.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/cleaning/__init__.py`](src/cleaning/__init__.py): Implementation or supporting configuration.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `clean` and explain the decision it makes?

The main walkthrough here is `clean(rows, fill='median', date_columns=(), flag_outliers=True)` in [`src/cleaning/clean.py`](src/cleaning/clean.py#L56).

```python
def clean(rows, fill="median", date_columns=(), flag_outliers=True):
    if fill not in STRATEGIES:
        raise CleaningError(f"fill must be one of {', '.join(sorted(STRATEGIES))}")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise CleaningError("rows must be a list of objects")
    original = copy.deepcopy(rows)
    report = {"renamed": {}, "dropped_duplicates": 0, "stripped": 0, "coerced": 0, "dates": 0, "filled": 0, "dropped_missing": 0, "outliers": []}

    renamed_rows = []
    for row in rows:
        renamed = {}
        for key, value in row.items():
            new_key = snake(key)
            if new_key != key:
                report["renamed"][key] = new_key
            renamed[new_key] = value
        renamed_rows.append(renamed)

    for row in renamed_rows:
        for key, value in list(row.items()):
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `', '.join`, `CleaningError`, `all`, `any`, `coerce`, `copy.deepcopy`, `dict.fromkeys`, `enumerate`, `isinstance`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `iso_date` have?

`iso_date(value)` is defined in [`src/cleaning/clean.py`](src/cleaning/clean.py#L29).

Its return expressions include:

- `None`
- `None`
- `datetime.strptime(value.strip(), fmt).date().isoformat()`

It uses `datetime.strptime`, `datetime.strptime(value.strip(), fmt).date`, `datetime.strptime(value.strip(), fmt).date().isoformat`, `isinstance`, `value.strip`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `CleaningError(f"fill must be one of {', '.join(sorted(STRATEGIES))}")` in [`src/cleaning/clean.py`](src/cleaning/clean.py#L58).
- `CleaningError('rows must be a list of objects')` in [`src/cleaning/clean.py`](src/cleaning/clean.py#L60).
- `CleaningError('input rows were modified')` in [`src/cleaning/clean.py`](src/cleaning/clean.py#L139).
- `CleaningError(f'{column} has a value that is not a known date format: {row[key]}')` in [`src/cleaning/clean.py`](src/cleaning/clean.py#L93).
- `HTTPException(status_code=422, detail=str(exc))` in [`src/cleaning/main.py`](src/cleaning/main.py#L28).
- `HTTPException(status_code=404, detail='workspace not found')` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L77).
- `HTTPException(status_code=404, detail='job not found')` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L100).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_clean.py`](tests/test_clean.py#L13) contains `test_dedupe_strip_and_fill`:

```python
def test_dedupe_strip_and_fill():
    rows = [
        {"name": " ada ", "score": 10},
        {"name": "ada", "score": None},
        {"name": " ada ", "score": 10},
    ]
    payload = post(rows).json()
    assert payload["dropped_duplicates"] == 1
    assert payload["filled"] == 1
    assert payload["rows"][0]["name"] == "ada"
    assert payload["rows"][1]["score"] == 10
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/cleaning/main.py`](src/cleaning/main.py#L19).
- `POST /clean` → `post_clean` in [`src/cleaning/main.py`](src/cleaning/main.py#L24).
- `GET /readyz` → `readyz` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L44).
- `POST /workspaces` → `create_workspace` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L49).
- `GET /workspaces` → `list_workspaces` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L66).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L73).
- `GET /jobs/{job_id}` → `get_job` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L96).
- `POST /jobs/{job_id}/approve` → `approve_job` in [`src/cleaning/ops.py`](src/cleaning/ops.py#L105).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `STRATEGIES` in [`src/cleaning/clean.py`](src/cleaning/clean.py); `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/cleaning/ops.py`](src/cleaning/ops.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `clean`?

In [`src/cleaning/clean.py`](src/cleaning/clean.py#L56), `clean(rows, fill='median', date_columns=(), flag_outliers=True)` receives the inputs. The function computes these intermediate values:

- `original = copy.deepcopy(rows)`
- `report = {'renamed': {}, 'dropped_duplicates': 0, 'stripped': 0, 'coerced': 0, 'dates': 0, 'filled': 0, 'dropped_missing': 0, 'outliers': []}`
- `renamed_rows = []`
- `unique = []`
- `keys = list(dict.fromkeys((key for row in unique for key in row)))`
- `numeric = [key for key in keys if any((isinstance(row.get(key), (int, float)) and (not isinstance(row.get(key), bool)) for row in unique))]`

Its result is defined by:

- `{'rows': unique, **report}`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/cleaning/clean.py`](src/cleaning/clean.py#L56) branches on:

- `fill not in STRATEGIES`
- `not isinstance(rows, list) or not all((isinstance(row, dict) for row in rows))`
- `fill == 'drop'`
- `flag_outliers`
- `rows != original`
- `row in unique`
- `fill != 'none'`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 14. What does the operations plane add, and where is its limit?

[`src/cleaning/ops.py`](src/cleaning/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
