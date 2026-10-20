"""Apply chosen replacement wording to the original contract text."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple


def apply_fixes(text: str, clauses: List[str], replacements: Dict[int, str]) -> Tuple[str, List[int]]:
    """Replace each clause (matched token-by-token, ignoring line wraps) with its new wording.

    Returns (revised text, indexes of clauses that could not be located).
    """
    out, pos, missed = [], 0, []
    for idx in sorted(replacements):
        pattern = re.compile(r"\s+".join(re.escape(t) for t in clauses[idx].split()))
        m = pattern.search(text, pos)
        if not m:
            missed.append(idx)
            continue
        out += [text[pos : m.start()], replacements[idx]]
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), missed
