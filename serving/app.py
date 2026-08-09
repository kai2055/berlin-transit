"""FastAPI service: predict whether a Berlin train will be more than 3 min late."""

import re
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

# Loading model and the exact training column order once, at startup
artifact = joblib.load(Path(__file__).parent / "model.joblib")
MODEL = artifact["model"]
COLUMNS = artifact["columns"]

app = FastAPI(title="Berlin Transit Delay Predictor")

class Train(BaseModel):
    line: str
    station_name: str
    planned_when: str


def build_row(train: Train) -> pd.DataFrame:
    """Turn one train into the same features the model was trained on"""
    ts = pd.Timestamp(train.planned_when)
    if ts.tzinfo is None:
        ts = ts.tz_convert("Europe/Berlin")

    ts = ts.tz_convert("Europe/Berlin")

    match = re.match(r"^([A-Za-z]+)", train.line)
    line_type = match.group(1) if match else "BUS"

    row = pd.DataFrame([{
        "hour": ts.hour,
        "day_of_week": ts.dayofweek,
        "is_weekend": int(ts.dayofweek >= 5),
        "station_name": train.station_name,
        "line_type": line_type,

    }])
    row = pd.get_dummies(row, columns=["station_name", "line_type"])
    return row.reindex(columns=COLUMNS, fill_value=0)



@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(train: Train):
    X = build_row(train)
    prob = float(MODEL.predict_proba(X)[0, 1])
    return {"probability_late": round(prob, 3), "will_be_late": prob >= 0.5}


