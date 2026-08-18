"""Streamlit dashboard: Berlintransit delay insights. + live predictor"""

from datetime import datetime, time

import pandas as pd
import requests
import streamlit as st
from google.cloud import bigquery

PROJECT = "berlin-transit-504417"
LOCATION = "us-central1"
API_URL = "https://transit-api-184545841057.us-central1.run.app/predict"

@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    client = bigquery.Client(project=PROJECT, location=LOCATION)
    query = """
        SELECT line, station_name, planned_when, delay_seconds
        FROM transit.int_departures_latest
        WHERE delay_seconds IS NOT NULL
    """

    return client.query(query).to_dataframe()

st.title("🚆 Berlin Transit Delay Intelligence")
st.caption("Live delay patterns across Berlin's network")

df = load_data()
df["line_type"] = df["line"].str.extract(r"^([A-Za-z]+)")[0].fillna("BUS")
df["hour"] = df["planned_when"].dt.tz_convert("Europe/Berlin").dt.hour

# Live predictor
st.subheader("Will your train be late?")
c1, c2 = st.columns(2)
line_in = c1.text_input("Line (e.g. RE3, U8, ICE 1001)", "RE3")
station_in = c2.selectbox("Station", sorted(df["station_name"].unique()),
                          key="pred_station")

c3, c4 = st.columns(2)
date_in = c3.date_input("Date")
time_in = c4.time_input("Scheduled time", time(8, 30))

if st.button("Predict"):
    planned = datetime.combine(date_in, time_in).isoformat() + "+2:00"
    payload = {"line": line_in, "station_name": station_in, "planned_when": planned}

    try:
        result = requests.post(API_URL, json=payload, timeout=60).json()
        prob = result["probability_late"]
        st.metric("Probability of being >3 min late", f"{prob:.0%}")
        if result["will_be_late"]:
            st.warning("⚠️ Likely late")
        else:
            st.success("✓  Likely on time")
    except Exception as e:
        st.error(f"Prediction failed: {e}")

st.divider()



st.sidebar.header("Filters")
stations = ["All"] + sorted(df["station_name"].unique())
station = st.sidebar.selectbox("Station", stations)
types = sorted(df["line_type"].unique())
chosen_types = st.sidebar.multiselect("service types", types, default=types)

view = df.copy()
if station != "All":
    view = view[view["station_name"] == station]
view = view[view["line_type"].isin(chosen_types)]

col1, col2 = st.columns(2)
col1.metric("Trips shown", f"{len(view):,}")
col2.metric("Average delay",
            f"{view['delay_seconds'].mean():.0f}sec" if len(view) else "-")

st.subheader("Average delay by service type")
by_type = view.groupby("line_type")["delay_seconds"].mean().sort_values(ascending=False)
st.bar_chart(by_type)

st.subheader("Average delay by hour of day (Berlin time)")
by_hour = view.groupby("hour")["delay_seconds"].mean()
st.bar_chart(by_hour)

