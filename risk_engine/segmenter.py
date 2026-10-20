"""Split raw contract text into clause-sized units (roughly one sentence each)."""
from __future__ import annotations

import re
from typing import List

_CLAUSE_START = re.compile(
    r"^\s*(?:section\s+)?(?:\d+(?:\.\d+)*[.)]?|\([a-z0-9]{1,4}\)|[A-Z]\.|article\s+[ivx\d]+)\s+",
    re.IGNORECASE,
)
_NUMBER_PREFIX = re.compile(r"^\s*(?:section\s+)?(?:\d+(?:\.\d+)*[.)]?|\([a-z0-9]{1,4}\))\s+", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.;!?])\s+(?=[A-Z(\"'“])")
MIN_CLAUSE_CHARS = 25
MAX_HEADING_CHARS = 60


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_heading(line: str) -> bool:
    """Short, unpunctuated line that is ALL CAPS or Title Case ("3. Termination")."""
    body = _NUMBER_PREFIX.sub("", line).strip()
    words = body.split()
    if not words or len(body) > MAX_HEADING_CHARS or len(words) > 8 or body.endswith((".", ";", ",", ":")):
        return False
    return body.isupper() or all(w[0].isupper() or not w[0].isalpha() for w in words if len(w) > 3)


def segment_clauses(text: str) -> List[str]:
    """Return clauses in document order.

    Blank lines and numbered items start new blocks, wrapped lines are re-joined,
    short heading lines are dropped, and each block is split into sentences so
    every obligation is scored on its own.
    """
    text = clean_text(text)
    blocks: List[str] = []
    current: List[str] = []

    def flush() -> None:
        if current:
            blocks.append(" ".join(current))
            current.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if _is_heading(stripped):
            flush()
            continue
        if current and _CLAUSE_START.match(stripped):
            flush()
        current.append(stripped)
    flush()

    clauses: List[str] = []
    for block in blocks:
        block = _NUMBER_PREFIX.sub("", block, count=1)
        for sent in _SENTENCE_SPLIT.split(block):
            sent = sent.strip()
            if len(sent) < MIN_CLAUSE_CHARS and clauses:
                clauses[-1] = f"{clauses[-1]} {sent}"
            elif sent:
                clauses.append(sent)
    return [c for c in clauses if len(c) >= MIN_CLAUSE_CHARS]
