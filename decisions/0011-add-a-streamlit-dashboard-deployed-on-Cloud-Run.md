# ADR-0011: Add a Streamlit dashboard, deployed on Cloud Run

- Status: Accepted
- Date: 2026-08-10

## Context
The model and the delay data are only reachable through code or the raw API.
We want a visual, human-friendly way to explore the patterns and try the
model — something a non-technical viewer (or a recruiter) can just open.

## Decision
Build a Streamlit dashboard: charts of delay by service type and by hour,
station/service filters, and a live "will it be late?" predictor. The
predictor calls the deployed model API over HTTP rather than bundling the
model, so the dashboard stays light and shows service-to-service use. Deploy
it as its own container on Cloud Run (staying single-cloud), and grant its
service account read access to BigQuery (dataViewer + jobUser).

## Alternatives considered
- Streamlit Community Cloud — off our GCP stack, and would need a
  service-account key in secrets to reach BigQuery; Cloud Run keeps it
  on-stack with cleaner in-project auth.
- Bundle the model in the dashboard instead of calling the API — duplicates
  the model and hides the service-to-service architecture.
- A heavier BI tool (Looker, etc.) — overkill; Streamlit is quick and Python.

## Consequences
A second public URL with charts, filters, and live predictions. It reads
BigQuery live (cached 10 min), so it reflects new data. Trade-off: a second
Cloud Run service to maintain (still ~€0, scales to zero), and it depends on
the API being up.