from fastapi.testclient import TestClient
from cleaning.main import app

def test_dedupe_strip_and_fill():
    rows = [
        {"name": " ada ", "score": 10},
        {"name": "ada", "score": None},
        {"name": " ada ", "score": 10},
    ]
    payload = TestClient(app).post("/clean", json={"rows": rows}).json()
    assert payload["dropped_duplicates"] == 1
    assert payload["filled"] == 1
    assert payload["rows"][0]["name"] == "ada"
    assert payload["rows"][1]["score"] == 10
