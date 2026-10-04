from fastapi.testclient import TestClient

from cleaning.clean import clean, snake
from cleaning.main import app

client = TestClient(app)


def post(rows, **extra):
    return client.post("/clean", json={"rows": rows, **extra})


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


def test_even_count_median_is_the_midpoint():
    rows = [{"score": 10}, {"score": 20}, {"score": None}]
    assert post(rows).json()["rows"][2]["score"] == 15


def test_column_names_become_snake_case():
    payload = post([{"First Name": "ada", "totalSpend": "5"}]).json()
    assert payload["renamed"] == {"First Name": "first_name", "totalSpend": "total_spend"}
    assert payload["rows"][0] == {"first_name": "ada", "total_spend": 5}


def test_numeric_strings_are_coerced():
    payload = post([{"amount": "1,250"}, {"amount": "3.5"}]).json()
    assert [row["amount"] for row in payload["rows"]] == [1250, 3.5]
    assert payload["coerced"] == 2


def test_dates_are_normalized_to_iso():
    payload = post([{"joined": "03/10/2026"}, {"joined": "2026/10/04"}], date_columns=["joined"]).json()
    assert [row["joined"] for row in payload["rows"]] == ["2026-10-03", "2026-10-04"]


def test_unknown_date_format_is_refused():
    response = post([{"joined": "next tuesday"}], date_columns=["joined"])
    assert response.status_code == 422


def test_drop_strategy_removes_rows_with_missing_numbers():
    payload = post([{"score": 1}, {"score": None}, {"score": 3}], fill="drop").json()
    assert payload["dropped_missing"] == 1
    assert len(payload["rows"]) == 2


def test_outliers_are_flagged_not_dropped():
    rows = [{"latency": value} for value in (100, 110, 105, 98, 102, 5000)]
    payload = post(rows).json()
    assert len(payload["rows"]) == 6
    assert [(item["column"], item["value"]) for item in payload["outliers"]] == [("latency", 5000)]


def test_input_rows_are_not_mutated():
    rows = [{"Name": " ada ", "score": None}]
    clean(rows)
    assert rows == [{"Name": " ada ", "score": None}]


def test_snake_handles_symbols():
    assert snake("Revenue ($)") == "revenue"
    assert snake("  ") == "column"


def test_unknown_fill_is_refused():
    assert post([{"score": 1}], fill="guess").status_code == 422
