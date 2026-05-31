"""The relay chain agents + the shadow answerer + the re-grounding repair step.

All prompts are deliberately plain. Gold is never shown to any of these.
"""
from __future__ import annotations

import re

from llm import BIG_MODEL, SMALL_MODEL, chat

LETTERS = "ABCD"


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
    sys = (
        "You are a relay agent. You did NOT see the original source. Rewrite the "
        "memo below in your own words to pass it on to the next agent, keeping it "
        "concise. You may compress, but try to preserve anything relevant to the "
        "question. Do not invent facts. Do not answer the question."
    )
    usr = (
        f"QUESTION: {question}\nCHOICES:\n{_format_choices(choices)}\n\n"
        f"MEMO:\n{prev_memo}\n\nRewrite the memo (<= 70 words)."
    )
    return chat(sys, usr, model=model, max_tokens=180)


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
