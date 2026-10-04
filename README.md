# Automated Data Cleaning Tool

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
