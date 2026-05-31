"""STEP 2 — the degradation gate (make-or-break).

Question: when an explanation is relayed through a chain of agents (no
re-grounding), does answer accuracy fall, AND do the models actually need the
passage (i.e. is the source-grounded answer better than answering blind)?

If RED -> stop, pivot. If GREEN -> run probe.py.

Runs three quick conditions on the same items:
  - source     : answer directly from the full source (ceiling; needs the model)
  - direct     : answer from question+choices only, NO source (blind floor)
  - relayed    : Explainer -> Relay1 -> Relay2 -> Answerer (naive relay)

Gate is GREEN if:  relayed_acc < source_acc  AND  source_acc > direct_acc + margin
(the chain loses signal, and the signal genuinely came from the passage).
"""
from __future__ import annotations

import argparse

from agents import answerer, explainer, relay
from data import load_items
from llm import BIG_MODEL


def answer_from_source(item, model):
    # ceiling: give the answerer the whole source as the "memo"
    return answerer(item.source, item.question, item.choices, model=model)


def answer_blind(item, model):
    return answerer("(no information provided)", item.question, item.choices, model=model)


def answer_relayed(item, model):
    m0 = explainer(item.source, item.question, item.choices, model=model)
    m1 = relay(m0, item.question, item.choices)
    m2 = relay(m1, item.question, item.choices)
    return answerer(m2, item.question, item.choices, model=model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=18)
    ap.add_argument("--margin", type=float, default=0.10)
    ap.add_argument("--model", default=BIG_MODEL)
    args = ap.parse_args()

    items = load_items(n=args.n)
    print(f"[sanity] {len(items)} items | model={args.model}\n")

    src_ok = blind_ok = relay_ok = 0
    for it in items:
        s = answer_from_source(it, args.model) == it.gold
        b = answer_blind(it, args.model) == it.gold
        r = answer_relayed(it, args.model) == it.gold
        src_ok += s; blind_ok += b; relay_ok += r
        print(f"{it.item_id:>12}  source={'Y' if s else 'n'} "
              f"blind={'Y' if b else 'n'} relayed={'Y' if r else 'n'}")

    n = len(items)
    sa, ba, ra = src_ok / n, blind_ok / n, relay_ok / n
    print("\n--- accuracy ---")
    print(f"source : {sa:.2f}")
    print(f"blind  : {ba:.2f}")
    print(f"relayed: {ra:.2f}")

    needs_source = sa > ba + args.margin
    relay_loses = ra < sa
    green = needs_source and relay_loses
    print("\n--- GATE ---")
    print(f"relay loses vs source?      {relay_loses}  ({ra:.2f} < {sa:.2f})")
    print(f"source beats blind by >{args.margin:.2f}? {needs_source}  ({sa:.2f} vs {ba:.2f})")
    print(f"\n>>> {'GREEN — proceed to probe.py' if green else 'RED — stop and pivot'} <<<")


if __name__ == "__main__":
    main()
