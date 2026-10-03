from fastapi import FastAPI
from cleaning.clean import clean

app = FastAPI()

@app.post("/clean")
def post_clean(body: dict):
    return clean(body["rows"])
