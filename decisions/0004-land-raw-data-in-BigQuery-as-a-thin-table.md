# ADR-0004: Land raw data in BigQuery as a thin table with a JSON column

- Status: Accepted
- Date: 2026-08-03

## Context
The raw VBB replies are deeply nested — each reply holds a list of
departures, and each departure has many fields. We need them in BigQuery
so we can work on them, but we haven't settled the final clean shape yet,
and we don't want a setup that breaks when the data varies.

## Decision
Load each raw file into a thin table (`departures_raw`): our three labels
as plain columns (`fetched_at`, `station_id`, `station_name`), plus the
entire untouched VBB reply in one JSON column (`response`). Don't flatten
the departures at load time. Follow ELT — load raw first, then transform
inside BigQuery with dbt later.

## Alternatives considered
- Auto-detect the full nested schema — spreads everything into columns
  automatically, but it's fragile: if fields vary or go missing across
  files, the guessed schema can break or silently drop data.
- Transform before loading (ETL) — more moving parts outside the
  warehouse; BigQuery does the transforming better and cheaper, and we'd
  lose an easy raw copy.
- External table (BigQuery reads the bucket files directly, no copy) —
  saves a little storage, but slower over many small files; our data is
  tiny, so a loaded copy is simpler and faster.

## Consequences
Raw landing is simple and sturdy: nothing lost, no guessing at the messy
shape, and dbt owns the final shape. Trade-offs: reading the JSON column
needs JSON functions until dbt flattens it, and we keep a second raw copy
in BigQuery on top of the bucket — fine, given the tiny size.