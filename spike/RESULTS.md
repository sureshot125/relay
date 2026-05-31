# Relay spike — results (2026-05-31)

Throwaway feasibility run. Models via OpenAI (substitute for W&B Inference, which
was unreachable from the build container). **Findings carry forward, code does not.**

- big model (explainer / answerer / shadow / reground): `gpt-4o-mini`
- relay model: `gpt-3.5-turbo`
- `RELAY_MAX_WORDS=25`, 3 relay hops, 15 passage-dependent items from RACE

## Gate (relay_sanity.py)

| run | source | blind | relayed | verdict |
|-----|--------|-------|---------|---------|
| natural (gpt-4o relay, no levers, full RACE) | 0.94 | 0.67 | **1.00** | **RED** — no loss |
| levered (selection + force-compression + weak relay + 3 hops) | 1.00 | 0.00 | **0.60** | **GREEN** — 40% loss |

Natural degradation was weak (strong models + short/easy passages). The result
exists **only under disclosed context pressure**: passage-dependent item
selection, hard relay compression (25 words), a weaker relay model, and 3 hops.
This is the licensed remediation lever, not a default — and it's the honest
headline: *loss appears under realistic compression pressure, not unconditionally.*

## Four-condition probe (probe.py) — the money result

| condition | accuracy | avg interventions | avg tokens |
|-----------|----------|-------------------|------------|
| naive | 0.60 | 0.00 | 247.9 |
| always_reground | 0.93 | 3.00 | 466.1 |
| adaptive | **0.80** | 1.00 | 326.5 |
| random_at_budget | 0.67 | 1.00 | 316.9 |

adaptive intervention rate 33% (threshold = 0.45, the 70th-pct risk).

**Decision-rule check (all four pass → GREENLIGHT):**
1. naive (0.60) < always (0.93) — loss exists, re-grounding helps. ✅
2. adaptive (0.80) > random_at_budget (0.67) **at equal budget** (1 interv. each) — the signal has decision value. ✅
3. adaptive uses fewer interventions than always (1 vs 3). ✅
4. ≥1 clean adaptive-fixes-naive case — found **4**. ✅

adaptive sits on a good frontier: ~⅔ of the always-reground gain at ~⅓ of the
extra cost, and a clear +13 pts over random at the same number of interventions.

## Clean demo case (race-735)
> Q: "We can know from the passage that the Internet bar ___."
> Gold: **D** (a place where some people may commit crimes)
> naive relay → **B** (should be made more convenient) ✗
> adaptive (re-grounded on a high-risk hop) → **D** ✓

(3 more in `demo_cases.jsonl`: race-800, race-4609, race-810.)

## Weakest parts (say these out loud)
- **n = 15, no statistics.** Differences are suggestive, not significant.
- **The effect is conditional.** Natural setting was RED; GREEN needs the levers.
  Pitch must be "loss under context pressure," not "loss always happens."
- **Selection is mildly circular** for the "needs the passage" claim (source=1.0 /
  blind=0.0 by construction). It's legitimate scoping, but disclose it.
- **adaptive < always (0.80 vs 0.93):** the signal picks good moments but misses
  some; lowering the threshold trades cost for fidelity toward the always bound.
- random barely beat naive (0.67 vs 0.60) at this budget — good for the story, but
  thin n means re-run with more items before leaning on it.

## For tomorrow's build
- Starting threshold ≈ **0.45** (gave 33% rate / ~1 intervention/item). Sweep it
  to draw the cost/fidelity frontier (the four-point scatter).
- Keep the levers but **state them**; consider weighting **answer-instability**
  over drift in `risk` (the operational signal is the more defensible one).
- Re-run at n ≥ 40 for the submission to firm up adaptive-vs-random.
