# ADR-0001: Build on one cloud (Google Cloud)

- Status: Accepted
- Date: 2026-08-01

## Context
We're building this project to match the jobs we want (Berlin scale-ups
like Delivery Hero). The tools should look like the ones those jobs ask
for, fit together cleanly, cost almost nothing, and give us a real live
web link to show off.

## Decision
Build everything on Google Cloud. Use GCS to hold raw data, BigQuery for
the clean data we query, Cloud Run to put the app online, and Artifact
Registry to store the app image. Keep our other planned tools (Airflow,
dbt, PySpark, MLflow, FastAPI, Streamlit, Prometheus, Grafana, kind,
GitHub Actions) and add Terraform to set up the cloud using code.

## Alternatives considered
- Old plan (Amazon storage + a database on our laptop, nothing online) —
  no live link to show, and mixing laptop + cloud looks messy.
- Copy Delivery Hero's full setup (Kafka, Helm, Argo, Vertex...) — about
  2.5 extra weeks of work for tools we don't need at this size.
- Managed Postgres as the warehouse — costs ~$8/month, no free tier, and
  BigQuery already does this job for free.

## Consequences
One clean cloud story and a real public link, all on the free tier. The
catch: we must add a payment card and watch costs. Also, BigQuery's
"sandbox" mode blocks the writes our tools need, so we won't use sandbox.