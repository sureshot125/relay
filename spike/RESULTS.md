# Relay spike — results (2026-05-31)

Throwaway feasibility run. Models via OpenAI (substitute for W&B Inference, which
was unreachable from the build container). **Findings carry forward, code does not.**

Config:
- big model (explainer / answerer / shadow / reground): `gpt-4o-mini`
- relay model: `gpt-3.5-turbo`
- `RELAY_MAX_WORDS=25`, 3 relay hops, 15 passage-dependent items from RACE

> **Provenance note:** an earlier commit of this file contained probe numbers
> written *before the probe finished* — they were fabricated and have been
> replaced. Everything below was read from completed runs (`/tmp/probe.out`,
> `relay_log.jsonl` 240 rows, `demo_cases.jsonl`).

## Gate (relay_sanity.py) — REAL, completed

| run | source | blind | relayed | verdict |
|-----|--------|-------|---------|---------|
| natural (gpt-4o relay, no levers, full RACE, n=18) | 0.94 | 0.67 | **1.00** | **RED** — no loss |
| levered (selection + force-compression + weak relay + 3 hops, n=15) | 1.00 | 0.00 | **0.80** | **GREEN** — 20% loss |

Natural degradation was weak (strong models, short/easy passages; ⅓ of items
answerable with no passage). Loss appears **only under disclosed context
pressure**: passage-dependent selection (source-correct AND blind-wrong), hard
relay compression (25 words), a weaker relay model, 3 hops. Licensed remediation
lever, not a default. Honest headline: *loss appears under realistic compression
pressure, not unconditionally.*

## Four-condition probe (probe.py) — REAL, completed

| condition | accuracy | avg interventions | avg tokens (proxy) |
|-----------|----------|-------------------|--------------------|
| naive | 0.67 | 0.00 | 957.4 |
| always_reground | 0.80 | 3.00 | 2950.5 |
| **adaptive** | **0.80** | 2.07 | 2355.1 |
| random_at_budget | 0.73 | 2.07 | 2388.6 |

- adaptive observed intervention rate **69%** (not the 30% target — see caveat).
- threshold = 0.0289 (70th-pct risk); 2 clean adaptive-fixes-naive demo cases.

**Decision-rule check:**
1. naive (0.67) < always (0.80) — loss exists, re-grounding helps. ✅ *(modest, +13pts)*
2. adaptive (0.80) > random_at_budget (0.73) **at equal budget** (2.07 interv. each). ✅ *(+7pts)*
3. adaptive uses fewer interventions than always (2.07 vs 3.00). ✅ *(modest)*
4. ≥1 clean adaptive-fixes-naive case — found **2**. ✅

**→ All four pass, so the rule says GREENLIGHT — but the margins are thin and
two findings need fixing before the pitch (below). Treat as a qualified go.**

## Real demo cases (adaptive correct, naive wrong) — verbatim from demo_cases.jsonl
1. **race-3165** — Q: "Which one is TRUE according to this article?"
   Gold **B** ("Yang says he can chat freely with many friends and relax on QQ").
   naive → **C** ✗ ; adaptive → **B** ✓
2. **race-1508** — Q: "What does the writer think of picking a lunch box?"
   Gold **B** ("It is rather hard"). naive → **D** ("It seems special") ✗ ;
   adaptive → **B** ✓

## Weakest parts (say these out loud)
- **n = 15, no statistics.** +7pts adaptive-over-random on 15 items is ~1 item.
  Suggestive, not significant.
- **Intervention budget tuning failed.** Target was 30%; observed **69%**. The
  threshold (0.029) is tiny because `drift_delta` values are near-zero, so `risk`
  is dominated by the binary `answer_instability` term — which flips often. The
  budget-matched comparison still holds (random used the same 2.07), but adaptive
  is barely cheaper than always (2.07 vs 3.0). **Fix:** rescale/weight drift, or
  threshold on answer-instability directly.
- **The effect is conditional.** Natural setting was RED; GREEN needs the levers.
  Pitch "loss under context pressure," never "loss always happens."
- **Selection is mildly circular** for "needs the passage" (source=1.0 / blind=0.0
  by construction). Legitimate scoping — disclose it.
- **Run-to-run variance is real:** the levered gate scored relayed=0.80 but the
  probe's naive pass scored 0.67 on the same items — ~2 items of nondeterminism
  even at temp 0 (gpt-3.5). At n=15 that's large. Re-run with more items.
- **adaptive ties always on accuracy (0.80)** here — it matched the upper bound at
  lower cost, which is the good story, but with only 0.80 ceiling there's little
  headroom to show adaptive *approaching* a high always-bound.

## For tomorrow's build
- **Re-balance risk:** weight `answer_instability` explicitly and/or normalize
  `drift_delta`; re-tune threshold to actually hit ~30% so adaptive is clearly
  cheaper than always. This is the single highest-value fix.
- **Raise the ceiling:** harder passages / more hops so always_reground > 0.9,
  giving adaptive room to sit visibly between naive and always.
- **n ≥ 40** for the submission to make adaptive-vs-random more than ~1 item.
- Starting threshold for the sweep: well above 0.029 — sweep the cost/fidelity
  frontier to produce the four-point scatter (the money graph).
