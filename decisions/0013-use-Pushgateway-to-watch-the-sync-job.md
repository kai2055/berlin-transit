# ADR-0013: Use Pushgateway to watch the sync job

- Status: Accepted
- Date: 2026-08-18

## Context
We want to watch our sync job the way real teams do — see how many rows it
loaded, how long it took, and whether it worked. The normal tool for this is
Prometheus, which *pulls*: every few seconds it visits a running service and
asks "what are your numbers right now?" That works for something always on,
like a web app. But our sync job is not always on. It wakes up, clones the
repo, loads BigQuery, and dies — the whole thing lasts a couple of minutes.
Prometheus checks every 15 seconds, so it would almost always knock when the
job is already dead, and even a lucky hit would find nothing left to read.

## Decision
Use Prometheus Pushgateway as a middleman. The sync job *pushes* its numbers
into the Pushgateway on its way out, and the Pushgateway — which is always on
— holds them. Prometheus then pulls from the Pushgateway instead of from the
job. The job can die happily; the numbers stay in the box. We push four
metrics (files uploaded, rows loaded, duration, success/fail), all as Gauges,
and show them in Grafana.

## Alternatives considered
- Point Prometheus straight at the sync job — does not work: the job is too
  short-lived to ever be scraped.
- Use Counters instead of Gauges — does not work here: the Pushgateway keeps
  only the *last* value pushed, so a counter would reset to its start value
  every run and never add up. Gauges (a fresh reading each run) are the right
  fit for a job that runs and exits.
- Google Cloud Monitoring only — free and already watching the deployed job,
  but it doesn't teach or show the Prometheus/Grafana tools that job ads ask
  for. We keep it for production and use Pushgateway/Grafana for the demo.

## Consequences
We get real dashboards and a clear story for why batch jobs need a different
setup than always-on services. Trade-offs to know: the Pushgateway holds its
data in memory, so restarting its container empties the box (a persistent
volume would fix this if we ever need it); and because it keeps only the last
push, these metrics show the *most recent* run, not a full history — which is
why the success panel is titled "Last Sync Status."