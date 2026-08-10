# ADR-0010: Serve the model as a containerised FastAPI app on Cloud Run

- Status: Accepted
- Date: 2026-08-09

## Context
The trained model needs to be usable by people and apps, not just runnable
in a local script. We want a real public URL, near-zero cost, and something
that fits the single-cloud GCP stack.

## Decision
- Wrap the model in a small FastAPI app with a `/predict` endpoint (plus a
  health check).
- Save the trained model and its feature-column list to `serving/model.joblib`,
  committed to the repo so the build is self-contained.
- Package it with Docker (`python:3.12-slim`).
- Deploy to Cloud Run with `gcloud run deploy --source`, which builds via
  Cloud Build and stores the image in Artifact Registry.
- Make the endpoint public (`--allow-unauthenticated`) — it exposes no
  sensitive data.

## Alternatives considered
- Build locally and push the image to Artifact Registry by hand — more steps;
  source-deploy is simpler and still lands the image in Artifact Registry.
- Load the model from GCS or the MLflow registry at runtime — cleaner, but
  more moving parts; committing a small model file keeps deployment simple.
- An always-on VM instead of Cloud Run — costs money when idle; Cloud Run
  scales to zero (free when unused).

## Consequences
A live public URL serving predictions at effectively €0 (Cloud Run scales to
zero; only a tiny ~€0.10/month Artifact Registry image cost). Trade-offs: the
model file lives in git (fine while small), and the deployed model is a
snapshot — we redeploy to update it. The API re-implements the small feature
engineering itself, so the container needs no BigQuery dependency.