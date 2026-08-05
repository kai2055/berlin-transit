# ADR-0006: Add dbt tests and first mart model; accept time-series "duplicates"

- Status: Accepted
- Date: 2026-08-05

## Context

With `stg_departures` built, we need to (1) guard data quality and
(2) produce the first analytical layer. We also discovered that
time-series transit data has a shape we hadn't fully accounted for.

## Decision

1. **Add dbt generic tests** to `stg_departures`:
   - `not_null` on `trip_id`, `planned_when`, `station_name`
   - `accepted_values` on `station_name` against the 14 watched stations

2. **Build `mart_delay_summary`** — first mart model aggregating
   average/max/min delay per `line`, `station_name`, `hour_of_day`.

3. **Attempt a composite uniqueness test** on
   `(trip_id, station_id, planned_when)`, then **remove it** after
   discovering the data legitimately contains the same train captured
   across multiple API calls as its delay evolves. The "duplicates"
   are valid time-series observations, not data quality defects.

## Alternatives considered

- Keep the composite uniqueness test and add `fetched_at` to the key.
  Rejected: this would pass trivially but mask the real insight that
  delays evolve over time. Better to model the data as it is.
- Write custom SQL tests instead of generic tests. Rejected: generic
  tests (`not_null`, `accepted_values`) are standard dbt patterns and
  sufficient for this stage.

## Consequences

- Data quality is now guarded by 4 passing tests.
- The project produces real analytical output (`mart_delay_summary`).
- We learned that `trip_id` alone is not unique — the same train appears
  multiple times across collection windows. This informs future models
  (e.g., delay-trend analysis can use these repeated observations).