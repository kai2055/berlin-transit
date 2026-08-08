"""Train a  'will this train be late?' classfier and evaluate it honestly"""

import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from xgboost import XGBClassifier

from pull_data import load_departures
from features import build_features

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

FEATURES = ["hour", "day_of_week", "is_weekend", "station_name", "line_type"]
LATE_THRESHOLD_SECONDS = 180 # "late" = more than 3 minutes


def main() -> None:
    df = build_features(load_departures())

    # Target: 1 if the train was more than 3 minutes late, else 0
    Y = (df["delay_seconds"] > LATE_THRESHOLD_SECONDS).astype(int)
    X = pd.get_dummies(df[FEATURES], columns=["station_name", "line_type"])

    log.info("Share of trains that are late: %.1f%%", Y.mean() * 100)

    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, random_state=42, stratify=Y
    )

    # Late trains are rare, so the models need to weigh them more heavily
    pos_weight = (Y_train == 0).sum() / (Y_train == 1).sum()
    model = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
                          random_state=42, scale_pos_weight=pos_weight,
                          eval_metric="logloss")
    model.fit(X_train, Y_train)

    probs = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(Y_test, probs)
    log.info("ROC-AUC:  %.3f    (0.5 = no better than guessing)", auc)

    preds = model.predict(X_test)
    print("\n", classification_report(Y_test, preds,
                                      target_names=["on time", "late"]))



if __name__ == "__main__":
    main()

    