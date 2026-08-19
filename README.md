# Berlin Transit Delay Intelligence

**An end-to-end data & ML engineering pipeline that predicts whether a Berlin train will be more than 3 minutes late — from live data collection to a deployed public API, dashboard, and full observability.**

[![CI](https://github.com/kai2055/berlin-transit/actions/workflows/ci.yml/badge.svg)](https://github.com/kai2055/berlin-transit/actions/workflows/ci.yml)

- **Live API:** https://transit-api-184545841057.us-central1.run.app
- **Live dashboard:** https://transit-dashboard-184545841057.us-central1.run.app

Built to mirror the stack of Berlin scale-ups (GCP, dbt, MLOps tooling). Every tool maps to a real production concern, and every major decision is written down in a plain-language [decision log](decisions/).

---

## What it does

Every ~10 minutes, a collector polls live departure data for 12 Berlin/Brandenburg (VBB) stations and banks the raw JSON. That data flows through storage, transformation, and modeling layers, ending in a model that answers one question — *"will this train be more than 3 minutes late?"* — served over a public API and explored through a live dashboard. The whole thing runs inside GCP's always-free tier at effectively zero cost.

---

## The stack

Grouped by what each layer does. Everything is single-cloud GCP.

| Layer | Tools |
|---|---|
| **Collection** | GitHub Actions (scheduled git-scraper), Python |
| **Storage** | Google Cloud Storage (raw vault), BigQuery (warehouse, ELT) |
| **Transformation** | dbt (staging -> intermediate -> mart, with tests), PySpark (lake-ETL) |
| **Modeling** | scikit-learn, XGBoost, MLflow (experiment tracking) |
| **Serving** | FastAPI, Docker, Cloud Run (public API) |
| **Dashboard** | Streamlit on Cloud Run (charts, filters, live predictor) |
| **Orchestration** | Cloud Run job + Cloud Scheduler (repo -> GCS -> BigQuery sync) |
| **Observability** | Prometheus, Pushgateway, Grafana |
| **Infrastructure** | Terraform (service account, IAM, Cloud Run job, scheduler as code) |
| **Kubernetes** | kind (local cluster: Deployment, Service, health probes) |
| **CI** | GitHub Actions (ruff linting on every push) |

---

## Engineering decisions worth calling out

These are the judgment calls, including the honest failures — documented rather than hidden.

**Regression lost to the baseline, so the problem was reframed.** The first model tried to predict exact delay in seconds. It honestly failed to beat a "just guess zero" baseline (MAE ~45s). Rather than force it, the problem was reframed as binary classification — *"more than 3 minutes late?"* — using XGBoost with `scale_pos_weight` for the class imbalance, reaching ROC-AUC 0.886. The failed regression is kept in the repo as part of the story.

**Service type is the strongest delay predictor.** Feature importance showed the kind of service (U-Bahn vs. RE vs. ICE) drives lateness more than station or time of day — a more useful finding than the raw accuracy number.

**Time-series "duplicates" are real data, not defects.** A uniqueness test on trip IDs failed, because the same train is legitimately captured across multiple polls as its delay evolves. Instead of masking that with a compound key, the data is modeled as it truly is, and deduplicated to the final delay per trip. (See ADR-0006, ADR-0007.)

**Batch jobs need Pushgateway, not direct scraping.** Prometheus pulls metrics from always-on services, but the sync job runs for a couple of minutes and exits — there's nothing to scrape. The job pushes its metrics to a Pushgateway on exit instead, using all-Gauge metrics (Pushgateway is last-write-wins, so counters can't accumulate). (See ADR-0013.)

**Kubernetes is a demonstration, not a need.** The app runs on Cloud Run already; kind proves the Kubernetes skill (Deployment, Service, probes) locally and for free, rather than paying for GKE nodes to run infrastructure the project doesn't require. (See ADR-0014.)

---

## Repo layout

```
collect.py          # Phase-0 collector (deliberately simple baseline)
orchestration/      # sync.py: repo -> GCS -> BigQuery (Cloud Run job)
transit/            # dbt project (staging, intermediate, mart models + tests)
ml/                 # feature building, training, MLflow tracking
serving/            # FastAPI app + Dockerfile + Kubernetes manifests
dashboard/          # Streamlit dashboard
spark/              # PySpark lake-ETL job
observability/      # Prometheus + Pushgateway + Grafana (docker-compose)
terraform/          # infrastructure as code
decisions/          # 14 ADRs — every major decision, in plain language
.github/workflows/  # CI (ruff linting)
```

---

## Running it yourself

The live services need nothing — just open the URLs above. To run pieces locally:

- **Observability stack:** `cd observability && docker compose up -d` (Grafana on `:3000`, Prometheus on `:9090`, Pushgateway on `:9091`)
- **API on Kubernetes:** build the image, `kind create cluster --name transit`, `kind load docker-image transit-api:local --name transit`, then `kubectl apply -f serving/`
- **Lint:** `ruff check .`

A payment card is required for GCP, but the project stays inside the always-free tier (GCS 5 GB, BigQuery 10 GB storage + 1 TB queries/month). A €1 budget alert acts as a tripwire.

---

## Decision log

Every architectural choice — including the ones that changed course — is recorded in [`decisions/`](decisions/) as a short, plain-language ADR. Fourteen so far, covering the cloud choice, the ELT approach, the regression-to-classification reframe, the observability pattern, the Kubernetes decision, and more.