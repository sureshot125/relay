# Relay spike — results (2026-05-31)

Throwaway feasibility run. Models via OpenAI (substitute for W&B Inference, which
was unreachable from the build container). **Findings carry forward, code does not.**

Config:
- big model (explainer / answerer / shadow / reground): `gpt-4o-mini`
- relay model: `gpt-3.5-turbo`
- `RELAY_MAX_WORDS=25`, 3 relay hops, 15 passage-dependent items from RACE

> **Provenance note:** an earlier version of this file contained probe numbers
> that were written before the probe had actually finished. Those were wrong and
> have been removed. Only numbers read from a completed run appear below.

## Gate (relay_sanity.py) — REAL, completed run

| run | source | blind | relayed | verdict |
|-----|--------|-------|---------|---------|
| natural (gpt-4o relay, no levers, full RACE, n=18) | 0.94 | 0.67 | **1.00** | **RED** — no loss |
| levered (selection + force-compression + weak relay + 3 hops, n=15) | 1.00 | 0.00 | **0.80** | **GREEN** — 20% loss |

Natural degradation was weak (strong models + short/easy passages; 1/3 of items
answerable with no passage at all). The loss appears **only under disclosed
context pressure**: passage-dependent item selection (source-correct AND
blind-wrong), hard relay compression (25 words), a weaker relay model, and 3 hops.
This is the licensed remediation lever, not a default. Honest headline: *loss
appears under realistic compression pressure, not unconditionally.*

Per-item (levered gate): 3 of 15 relayed wrong (race-3165, race-944, race-4859).

## Four-condition probe (probe.py)

PENDING — see RESULTS_PROBE.md once the completed run is recorded. (The probe is a
long sequential run of hundreds of API calls; the first foreground attempt was
killed by a command timeout after the naive pass. Re-running to completion.)

## Weakest parts (say these out loud)
- **n = 15, no statistics.** Any differences will be suggestive, not significant.
- **The effect is conditional.** Natural setting was RED; GREEN needs the levers.
  Pitch must be "loss under context pressure," not "loss always happens."
- **Selection is mildly circular** for the "needs the passage" claim (source=1.0 /
  blind=0.0 by construction). Legitimate scoping, but disclose it.
- Gate margin is modest (0.80 vs 0.85 threshold = GREEN, but only 3 wrong items).
  Re-run at higher n / more hops to firm up before leaning on it.

## For tomorrow's build
- Re-run at n ≥ 40 for the submission.
- Consider weighting **answer-instability** over drift in `risk` (the operational
  signal is the more defensible one); the observed risk threshold was very small
  (~0.03), i.e. drift_delta values are tiny — worth rebalancing.
