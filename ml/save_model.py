"""Train the final model on all data and save it for serving."""

import logging
from pathlib import Path
import joblib
import pandas as pd
from xgboost import XGBClassifier

from pull_data import load_departures
from features import build_features

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

FEATURES = ["hour", "day_of_week", "is_weekend", "station_name", "line_type"]
LATE_THRESHOLD_SECONDS = 180
PARAMS = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.1}

def main() -> None:
    df = build_features(load_departures())
    Y = (df["delay_seconds"] > LATE_THRESHOLD_SECONDS).astype(int)
    X = pd.get_dummies(df[FEATURES], columns=["station_name", "line_type"])

    pos_weight = (Y == 0).sum() / (Y == 1).sum()
    model = XGBClassifier(**PARAMS, random_state=42,
                          scale_pos_weight=pos_weight, eval_metric="logloss")
    model.fit(X, Y)

    Path("serving").mkdir(exist_ok=True)
    joblib.dump({"model": model, "columns": list(X.columns)},
                "serving/model.joblib")
    log.info("Saved model + %d feature columns to serving/model.joblib",
             len(X.columns))


if __name__ == "__main__":
    main()


    