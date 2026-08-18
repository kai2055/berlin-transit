"""Train a 'will this train be late' classfier, tracked with MLflow.  """

import logging

import mlflow
import pandas as pd
from features import build_features
from pull_data import load_departures
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

FEATURES = ["hour", "day_of_week", "is_weekend", "station_name", "line_type"]
LATE_THRESHOLD_SECONDS = 180
PARAMS = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.1}

def main() -> None:
    df = build_features(load_departures())
    Y = (df["delay_seconds"] > LATE_THRESHOLD_SECONDS).astype(int)
    X = pd.get_dummies(df[FEATURES], columns=["station_name", "line_type"])

    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, random_state=42, stratify=Y
    )
    pos_weight = (Y_train == 0).sum() / (Y_train == 1).sum()

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("berlin-transit-lateness")
    with mlflow.start_run():
        model = XGBClassifier(**PARAMS, random_state=42,
                              scale_pos_weight=pos_weight,
                              eval_metric="logloss")
        model.fit(X_train, Y_train)

        probs = model.predict_proba(X_test)[:, 1]
        preds = model.predict(X_test)

        metrics = {
            "roc_auc": roc_auc_score(Y_test, probs),
            "precision_late": precision_score(Y_test, preds, pos_label=1),
            "recall_late": recall_score(Y_test, preds, pos_label=1),
            "f1_late": f1_score(Y_test, preds, pos_label=1),
        }

        mlflow.log_params(PARAMS)
        mlflow.log_param("late_threshold_seconds", LATE_THRESHOLD_SECONDS)
        mlflow.log_metrics(metrics)

        log.info("Logged run. ROC-AUC: %.3f", metrics["roc_auc"])
        print("\n", classification_report(Y_test, preds,
                                          target_names=["on time", "late"]))


if __name__ == "__main__":
    main()



