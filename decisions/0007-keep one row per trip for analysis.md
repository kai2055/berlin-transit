# ADR-0006: Keep one row per trip for analysis (deduplicate to the final delay)

- Status: Accepted
- Date: 2026-08-08

## Context
The staging model has one row per capture, and the same train appears in
many 10-minute captures, its delay updating each time. Our first mart
averaged over all those captures — which over-counted trains we happened to
watch longer, and mixed early guesses with final delays. The numbers weren't
trustworthy. Hours were also in UTC, not Berlin time.

## Decision
Add an intermediate model (`int_departures_latest`) that keeps only the last
capture per trip per station — the final, realized delay — so each trip
counts once. Marts build on this. Staging still keeps every capture. Compute
hours in Berlin local time.

## Alternatives considered
- Count every capture (what we started with) — inflates counts and blends
  evolving guesses with final delays; misleading averages.
- Delete the repeated captures from staging — would throw away the
  delay-evolution history, which is valuable (e.g. for real-time prediction
  later). So we keep all captures in staging and dedupe only downstream.

## Consequences
Per-trip stats are now trustworthy, and the full capture history stays
available in staging for other uses. Cost: one more model to maintain, and
"final delay" is the last capture we took (possibly a few minutes before
actual departure) — close enough for now.