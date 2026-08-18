"""Show which features drive the 'late' prediction """

import logging

import pandas as pd
from features import build_features
from pull_data import load_departures
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)



FEATURES = ["hour", "day_of_week", "is_weekend", "station_name", "line_type"]
LATE_THRESHOLD_SECONDS = 180

def main() -> None:
    df = build_features(load_departures())
    Y = (df["delay_seconds"] > LATE_THRESHOLD_SECONDS).astype(int)
    X = pd.get_dummies(df[FEATURES], columns=["station_name", "line_type"])

    X_train, _, Y_train,  _ = train_test_split(
        X, Y, test_size=0.2, random_state=42, stratify=Y
    )
    pos_weight = (Y_train == 0).sum() / (Y_train == 1).sum()
    model = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
                          random_state=42, scale_pos_weight=pos_weight,
                          eval_metric="logloss")
    model.fit(X_train, Y_train)

    importance = (
        pd.Series(model.feature_importances_, index=X.columns)
        .sort_values(ascending=False)
        .head(15)
    )
    print("\nTop 15 features driving 'late' predictions:\n")
    print(importance.to_string())


if __name__ == "__main__":
    main()



