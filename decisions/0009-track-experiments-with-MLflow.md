# ADR-0009: Track experiments with MLflow

- Status: Accepted
- Date: 2026-08-08

## Context
We're training models and will tune them over time (thresholds, features,
settings). Without a record, comparing attempts means scribbling scores in a
notebook and losing track of what produced what.

## Decision
Use MLflow to track experiments. The classifier logs its settings (parameters)
and scores (ROC-AUC, precision, recall, f1) on every run, under an experiment
named `berlin-transit-lateness`. Runs are browsable in the local MLflow UI.

## Alternatives considered
- Manual logging (notebook, spreadsheet, print statements) — no structure,
  easy to lose, doesn't scale past a few runs.
- Weights & Biases or similar hosted trackers — heavier, cloud-hosted, and
  MLflow is the common open-source standard the target roles list.

## Consequences
Every training run is recorded and comparable, so we can see whether a change
actually helped. Local run data (`mlruns/`, `mlflow.db`) stays out of git.
Trade-off: currently tied to a local tracking store; if we later want runs
shared or persisted in the cloud, we'd point MLflow at a remote backend.