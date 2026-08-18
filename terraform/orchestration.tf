# =============================================================================
# ORCHESTRATION LAYER: Cloud Run Job + Cloud Scheduler
# Adds automated sync: GitHub repo -> GCS -> BigQuery, running every hour.
# Region: us-central1  |  Repo: public (no token needed)
# =============================================================================


variable "github_repo" {
  description = "GitHub repo in format owner/repo"
  type        = string
  default     = "kai2055/berlin-transit"
}

variable "bucket_name" {
  description = "Name of your existing GCS raw vault bucket"
  type        = string
  default     = "berlin-transit-504417xx"
}

locals {
  project_id = "berlin-transit-504417"
  region     = "us-central1"
}

# -- ARTIFACT REGISTRY REPOSITORY --
resource "google_artifact_registry_repository" "transit" {
  location      = local.region
  repository_id = "transit"
  description   = "Docker images for transit pipeline components"
  format        = "DOCKER"
}

# -- SERVICE ACCOUNT --
resource "google_service_account" "sync_runner" {
  account_id   = "transit-sync-runner"
  display_name = "Transit data sync runner"
}

# -- IAM PERMISSIONS --


resource "google_storage_bucket_iam_member" "sync_storage" {
  bucket = var.bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.sync_runner.email}"
}


resource "google_project_iam_member" "sync_bq" {
  project = local.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.sync_runner.email}"
}


resource "google_project_iam_member" "sync_bq_jobuser" {
  project = local.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.sync_runner.email}"
}


resource "google_project_iam_member" "scheduler_invoker" {
  project = local.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.sync_runner.email}"
}

# -- CLOUD RUN JOB --
resource "google_cloud_run_v2_job" "sync" {
  name     = "transit-sync"
  location = local.region

  template {
    template {
      service_account = google_service_account.sync_runner.email

      containers {
        image = "${local.region}-docker.pkg.dev/${local.project_id}/transit/sync:latest"

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        env {
          name  = "GCP_PROJECT"
          value = local.project_id
        }
        env {
          name  = "GCS_BUCKET"
          value = var.bucket_name
        }
        env {
          name  = "BQ_DATASET"
          value = "transit_raw"
        }
        env {
          name  = "BQ_TABLE"
          value = "departures_raw"
        }
        env {
          name  = "GITHUB_REPO"
          value = var.github_repo
        }
      }
    }
  }
}

# -- CLOUD SCHEDULER --
resource "google_cloud_scheduler_job" "sync" {
  name             = "transit-sync-hourly"
  description      = "Trigger transit data sync every hour"
  schedule         = "0 * * * *"
  time_zone        = "Europe/Berlin"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://${local.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${local.project_id}/jobs/${google_cloud_run_v2_job.sync.name}:run"

    oauth_token {
      service_account_email = google_service_account.sync_runner.email
    }
  }
}