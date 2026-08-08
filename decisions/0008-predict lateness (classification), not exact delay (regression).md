# ADR-0007: Predict lateness (classification), not exact delay (regression)

- Status: Accepted
- Date: 2026-08-08

## Context
The goal is to predict delays. We first tried predicting the exact delay in
seconds (regression). But most trains are exactly on time (median delay = 0),
so a model that just guesses 0 is very hard to beat — and our regression model
couldn't beat it. A specific train's delay depends on real-time factors our
features don't capture.

## Decision
Reframe as a yes/no question — "will this train be more than 3 minutes late?"
— and train a classifier. Judge it mainly by ROC-AUC (honest for imbalanced
data), not accuracy.

## Alternatives considered
- Keep regression and add more features — low ceiling; exact seconds are
  largely unpredictable from static features, so likely wasted effort.
- Keep regression as-is — it can't beat the trivial "guess 0" baseline.

## Consequences
The classifier found real signal (ROC-AUC ~0.89) and reliably ranks risky
trains. It's also more useful (riders care "is it late?"). We accept a
precision/recall trade-off — it catches most late trains but with false
alarms — tunable by threshold. Accuracy is deliberately not the headline.