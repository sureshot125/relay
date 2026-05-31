"""The relay chain agents + the shadow answerer + the re-grounding repair step.

All prompts are deliberately plain. Gold is never shown to any of these.
"""
from __future__ import annotations

import os
import re

from llm import BIG_MODEL, SMALL_MODEL, chat

LETTERS = "ABCD"

# Force-compression lever: hard word budget on relay memos, modelling real
# context pressure. Used only because natural degradation was weak (see README).
RELAY_MAX_WORDS = int(os.environ.get("RELAY_MAX_WORDS", "25"))


def _format_choices(choices: list[str]) -> str:
    return "\n".join(f"{LETTERS[i]}. {c}" for i, c in enumerate(choices))


def explainer(source: str, question: str, choices: list[str], model: str = BIG_MODEL) -> str:
    sys = (
        "You are the first agent in a relay. You see a source passage and the "
        "question that will later be answered by someone who will NOT see the "
        "passage. Write a concise handoff memo that preserves the facts needed to "
        "answer the question. Do not answer the question; just relay what matters."
    )
    usr = (
        f"SOURCE:\n{source}\n\n"
        f"QUESTION: {question}\nCHOICES:\n{_format_choices(choices)}\n\n"
        "Write the handoff memo (<= 80 words)."
    )
    return chat(sys, usr, model=model, max_tokens=200)


def relay(prev_memo: str, question: str, choices: list[str], model: str = SMALL_MODEL) -> str:
    # Under tight context pressure the relay must compress hard; it is NOT shown
    # the question (it doesn't know which detail will matter) -> realistic loss.
    sys = (
        "You are a relay agent passing a note to the next person. You did NOT see "
        "the original source. You are under a strict length limit. Summarize the "
        "memo below as briefly as possible in your own words. Do not invent facts."
    )
    usr = (
        f"MEMO:\n{prev_memo}\n\n"
        f"Rewrite it in at most {RELAY_MAX_WORDS} words."
    )
    return chat(sys, usr, model=model, max_tokens=max(40, RELAY_MAX_WORDS * 3))


def _parse_letter(text: str) -> int:
    m = re.search(r"\b([ABCD])\b", text.upper())
    return LETTERS.index(m.group(1)) if m else 0


def answerer(memo: str, question: str, choices: list[str], model: str = BIG_MODEL) -> int:
    """Final answerer (also used as the shadow answerer). Returns 0..3. No gold."""
    sys = (
        "Answer the multiple-choice question using ONLY the memo. Reply with a "
        "single letter A, B, C, or D and nothing else."
    )
    usr = (
        f"MEMO:\n{memo}\n\nQUESTION: {question}\nCHOICES:\n{_format_choices(choices)}\n\n"
        "Answer (one letter):"
    )
    out = chat(sys, usr, model=model, temperature=0.0, max_tokens=4)
    return _parse_letter(out)


def reground(memo: str, question: str, choices: list[str], chunks: list[str],
             model: str = BIG_MODEL) -> str:
    """Repair step: correct the memo against the question-relevant source chunks."""
    sys = (
        "You are a grounding agent. You are given a memo plus the source passages "
        "most relevant to the question. Correct and complete the memo so it is "
        "fully supported by the source. Add back any dropped detail needed to "
        "answer the question. Use ONLY the source. Do not answer the question."
    )
    usr = (
        f"QUESTION: {question}\nCHOICES:\n{_format_choices(choices)}\n\n"
        f"CURRENT MEMO:\n{memo}\n\n"
        f"SOURCE (question-relevant excerpts):\n" + "\n---\n".join(chunks) +
        "\n\nWrite the corrected memo (<= 90 words)."
    )
    return chat(sys, usr, model=model, max_tokens=220)
