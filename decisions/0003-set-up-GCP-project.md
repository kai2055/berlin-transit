# ADR-0003: Set up GCP — dedicated project, pay-as-you-go, budget guard

- Status: Accepted
- Date: 2026-08-03

## Context
Our storage (GCS) and warehouse (BigQuery) both need an active billing
account. The old free trial is used up, so there's no $300 buffer left.
We also run another project on the same account, so resources and costs
could easily get tangled.

## Decision
- Make a separate project (`berlin-transit`) just for this work, so its
  resources and costs stay isolated.
- Run it pay-as-you-go, staying inside the always-free tier.
- Add a €1 budget alert on the project as an early warning.
- Put the storage bucket in us-central1 (a free-tier region) so BigQuery
  can sit next to it, also free.

## Alternatives considered
- Reuse the existing ML-pipeline project — mixes two projects' resources
  and costs; harder to track and to tear down cleanly.
- Wait for another free trial — not possible; one per person.
- A European region for the bucket — closer to us, but loses the free
  tier (bills from the first byte).

## Consequences
Clean separation and near-zero cost. The trade-off: no credit cushion, so
a mistake past the free tier bills real money — softened by staying inside
free limits, the budget alert, and checking each chargeable step. Note the
alert warns; it does not cap spending.