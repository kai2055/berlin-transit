"""Pull clean departure data from BigQuery into pandas and take a look"""

import logging
import pandas as pd
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

PROJECT = "berlin-transit-504417"
LOCATION = "us-central1"

def load_departures() -> pd.DataFrame:
    """Load one row per trip (deduped final delays) from the warehouse"""
    client = bigquery.Client(project=PROJECT, location=LOCATION)
    query = """
        SELECT line, station_name, direction, planned_when, delay_seconds
        FROM transit.int_departures_latest
        WHERE delay_seconds IS NOT NULL

    """
    log.info("Querying BigQuery...")
    df = client.query(query).to_dataframe()
    log.info("Loaded %d rows, %d columns", df.shape[0], df.shape[1])
    return df

if __name__ == "__main__":
    df = load_departures()
    print(df.head(10))
    print("\nShape:", df.shape)
    print("\nDelay stats (seconds):")
    print(df["delay_seconds"].describe())
