# ADR-0005: Use dbt for transformation, with a thin staging model

- Status: Accepted
- Date: 2026-08-03

## Context
The raw table holds one row per API call, with all the departures bundled
inside a JSON blob. We need to turn that into clean, tidy rows — one per
train — that analysis and models can use. We also want the transformation
to be code: versioned in git, testable, and standard for the roles we aim at.

## Decision
- Use **dbt** (dbt-bigquery) for the Transformation layer. Transformations
  are SQL "models" that dbt builds inside BigQuery.
- Register the raw table (`transit_raw.departures_raw`) as a dbt **source**.
- First model `stg_departures` uses `UNNEST` + JSON functions to flatten the
  bundled departures into one row per train, with delay, line, direction,
  station, and planned/actual times as proper numbers and timestamps.
- Local auth via **OAuth** (Application Default Credentials) — no
  service-account key file to manage.
- The dbt project lives in the repo (`transit/`); the connection profile
  lives outside it (`~/.dbt/profiles.yml`), so credentials aren't committed.

## Alternatives considered
- Hand-written SQL run manually — works, but no dependency tracking, tests,
  docs, or version discipline. dbt is the standard the target roles use.
- Flatten during load (in the collector or the bq load) — mixes collection
  with shaping and loses the "keep raw faithful" separation. ELT keeps raw
  untouched and transforms in the warehouse.
- Service-account key file for auth — an extra secret to store and protect;
  OAuth/ADC is simpler and safe for local development.

## Consequences
Transformation is now code — versioned, reviewable, reproducible — and clean
tables build from the raw with one command (`dbt run`). Staging models are
views: no storage cost, and they always reflect the latest raw. Trade-off:
local OAuth ties runs to a logged-in user; when we automate with Airflow,
we'll switch to a service account.