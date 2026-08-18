"""Turn raw departure data into model-ready features."""
import logging

import pandas as pd
from pull_data import load_departures

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-based and line-type features to the raw departures."""
    out = df.copy()

    # Convert the planned time to Berlin local, then pull time features.
    berlin_time = out["planned_when"].dt.tz_convert("Europe/Berlin")
    out["hour"] = berlin_time.dt.hour
    out["day_of_week"] = berlin_time.dt.dayofweek          # 0 = Monday
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)

    # The line string mixes names (U8) with train numbers (ICE 1105).
    # Extract just the type prefix — that's what actually predicts delay.
    out["line_type"] = out["line"].str.extract(r"^([A-Za-z]+)")[0].fillna("BUS")

    return out


if __name__ == "__main__":
    df = load_departures()
    feats = build_features(df)
    cols = ["line", "line_type", "station_name", "hour",
            "day_of_week", "is_weekend", "delay_seconds"]
    print(feats[cols].head(15))
    print("\nLine types found:")
    print(feats["line_type"].value_counts())