"""Streamlit dashboard: Berlin transit delay insights."""

import pandas as pd
import streamlit as st
from google.cloud import bigquery

PROJECT = "berlin-transit-504417"
LOCATION = "us-central1"

@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    """Pull one row per trip (final delays) from BigQuery"""
    client = bigquery.Client(project=PROJECT, location=LOCATION)
    query = """
        SELECT line, station_name, planned_when, delay_seconds
        FROM transit.int_departures_latest
        WHERE delay_seconds IS NOT NULL
    """
    return client.query(query).to_dataframe()


st.title("🚆 Berlin Transit Delay Intelligence ")
st.caption("Live delay patterns across Berlin's network")

df = load_data()

# Deriving service type and Berlin hour 
df["line_type"] = df["line"].str.extract(r"^([A-Za-z]+)")[0].fillna("BUS")
df["hour"] = df["planned_when"].dt.tz_convert("Europe/Berlin").dt.hour

col1, col2 = st.columns(2)
col1.metric("Trips observed", f"{len(df):,}")
col2.metric("Average delay", f"{df['delay_seconds'].mean():.0f} sec")

st.subheader("Average delay by service type")
by_type = df.groupby("line_type")["delay_seconds"].mean().sort_values(ascending=False)
st.bar_chart(by_type)

st.subheader("Average delay by hour of day (Berlin time)")
by_hour = df.groupby("hour")["delay_seconds"].mean()
st.bar_chart(by_hour)
