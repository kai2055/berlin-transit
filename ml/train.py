"""Train s first delay-prediction model"""

import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

from pull_data import load_departures
from features import build_features

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

FEATURES = ["hour", "day_of_week", "is_weekend", "station_name", "line_type"]
TARGET = "delay_seconds"


def main() -> None:
    df = build_features(load_departures())

    # category columns into numeric 0/1 columns; keep numbers as-is
    X = pd.get_dummies(df[FEATURES], columns=["station_name", "line_type"])
    Y = df[TARGET]

    # Holding back 20% of trips to test on data 
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(n_estimators=200, max_depth=5,
                         learning_rate=0.1, random_state=42,
                         objective="reg:absoluteerror")
    model.fit(X_train, Y_train)

    preds = model.predict(X_test)
    model_mae = mean_absolute_error(Y_test, preds)

    baseline_mae = mean_absolute_error(Y_test, [0] * len(Y_test))

    log.info("Model MAE:                %.1f seconds", model_mae)
    log.info("Baseline MAE (guess 0):   %.1f seconds", baseline_mae)
    log.info("Beat baseline by:         %.1f%%",
             (baseline_mae - model_mae) / baseline_mae * 100)



if __name__ == "__main__":
    main()


