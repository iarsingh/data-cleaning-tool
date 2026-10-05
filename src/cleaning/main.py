from cleaning.ops import router as ops_router
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cleaning.clean import CleaningError, clean

app = FastAPI()
app.include_router(ops_router, prefix="/v1")


class CleanBody(BaseModel):
    rows: list[dict] = Field(max_length=50_000)
    fill: str = "median"
    date_columns: list[str] = Field(default_factory=list)
    flag_outliers: bool = True


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/clean")
def post_clean(body: CleanBody):
    try:
        return clean(body.rows, body.fill, body.date_columns, body.flag_outliers)
    except CleaningError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
