# ADR-0014: Run Kubernetes locally with kind, not GKE

- Status: Accepted
- Date: 2026-08-19

## Context
The jobs we're targeting ask for Kubernetes, so we want to show we can deploy
to it and explain how it works. But our app already runs fine on Cloud Run,
so Kubernetes here is about proving the skill, not about making the system
work better. We also have to keep cost near zero.

## Decision
Use kind ("Kubernetes in Docker") to run a local, single-node cluster on the
laptop. Build the FastAPI image locally, load it straight into the cluster
(no registry), and deploy it with a Deployment (keep one healthy copy alive),
a Service (a stable address to reach it), and liveness/readiness probes
(health checks). Prove it works by calling /predict from inside the cluster.
Keep the manifests (deployment.yaml, service.yaml) in the repo as the real
artifact; the cluster itself is throwaway and rebuilt on demand.

## Alternatives considered
- GKE (real Kubernetes on Google Cloud) — the nodes always cost money, even
  with one free cluster's management fee waived. Not worth it to demonstrate
  manifests we can show just as well locally.
- Skip Kubernetes entirely and rely on Cloud Run — loses a keyword that shows
  up on almost every target job, and the "I can drive a cluster" story.
- Pull the image from Artifact Registry into kind — needs extra auth wiring
  and touches GCP. Loading the local image with `kind load` is simpler and
  fully free.

## Consequences
A real, defensible Kubernetes story — Deployment, Service, probes, and a live
prediction served from a Pod — at zero cost. Trade-offs: it's a single-node
local demo, not production (no autoscaling, no real ingress), and the image
uses `imagePullPolicy: Never`, which only works because we hand-load it into
kind. The cluster is disposable; recreating it is create → load → apply.