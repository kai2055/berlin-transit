# ADR-0002: Collect data now with a GitHub Action

- Status: Accepted
- Date: 2026-08-01

## Context
Live delay data only exists in the moment. Every hour we don't collect is
data lost forever. The proper cloud pipeline isn't ready yet and needs the
payment card set up first.

## Decision
Collect data now with a GitHub Action: a small Python script that runs
every ~10 minutes and saves the raw data straight into the repo.

## Alternatives considered
- A script on our own laptop — only runs when the laptop is awake.
- Wait for the full cloud pipeline — loses data we can't get back while
  we build it.

## Consequences
Data starts saving right away, on its own, for free. This is temporary:
we'll copy it into Google Cloud later and replace it with the proper
Airflow setup. Needs a public repo (to stay free), and we should check now
and then that GitHub hasn't paused the schedule (it pauses after 60 idle
days).