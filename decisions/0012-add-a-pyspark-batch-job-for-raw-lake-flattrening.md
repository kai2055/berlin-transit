# ADR-0012: Add a PySpark batch job for raw-lake flattening

- Status: Accepted
- Date: 2026-08-10

## Context
PySpark was in the v1.5 stack for batch transforms. The data is small — dbt
handles the warehouse transforms fine — so Spark isn't needed for performance.
But Spark is a common job requirement, so we want a genuine Spark job rather
than dropping it.

## Decision
Add a PySpark batch job (spark/flatten_departures.py) that reads the raw JSON
capture files, explodes the nested departures array, flattens them into clean
columns, coalesces to one partition, and writes parquet. It runs in a Spark
Docker container (no local Java needed). This plays the "lake ETL" role —
Spark processing the raw files — alongside dbt, which keeps the
warehouse-modelling role.

## Alternatives considered
- Drop PySpark entirely (proportionality) — honest, but loses a keyword the
  target roles often list.
- Use Spark for feature engineering or aggregation — those overlap pandas and
  SQL/dbt, the more natural tools; flattening nested JSON is what Spark is
  genuinely best at, so it's the most honest demonstration.
- Read from GCS and write back to GCS/BigQuery — more production-real, but
  needs connector jars + credentials in the container; local files keep this
  first version simple and free.

## Consequences
A real, working Spark job showing the core skills (read JSON, explode arrays,
select nested fields, coalesce, write parquet). Stated honestly: at this data
scale it's a skill demonstration running parallel to dbt, not a load-bearing
step. Could be upgraded to read/write GCS to make it production-wired.