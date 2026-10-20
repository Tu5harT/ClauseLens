"""Combine segmentation, rule scoring and the ML classifier into a report."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

from .rules import CATEGORIES, CATEGORY_BY_NAME, score_category
from .segmenter import segment_clauses
from . import classifier

HIGH, MEDIUM, LOW = 0.60, 0.35, 0.20  # score thresholds per clause
ML_WEIGHT = 0.30  # how much the classifier probability nudges a rule score
ML_ONLY_MIN_PROB = 0.70
ML_ONLY_SCORE = 0.22
_MUTUAL = re.compile(r"\b(mutual(ly)?|either party|each party|both parties)\b", re.IGNORECASE)

POINTS = {"High": 10, "Medium": 4, "Low": 1}
LEVEL_ORDER = {"High": 3, "Medium": 2, "Low": 1}


def level_for(score: float) -> Optional[str]:
    if score >= HIGH:
        return "High"
    if score >= MEDIUM:
        return "Medium"
    if score >= LOW:
        return "Low"
    return None


@dataclass
class Finding:
    index: int
    text: str
    category: str
    level: str
    score: float
    explanation: str
    recommendation: str
    source: str  # "rules", "rules+ml" or "ml"
    also: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ContractReport:
    clauses: List[Tuple[str, Optional[Finding]]]
    findings: List[Finding]
    overall_score: int
    overall_level: str
    category_counts: Dict[str, int]
    level_counts: Dict[str, int]

    @property
    def total_clauses(self) -> int:
        return len(self.clauses)


def _analyze_clause(index: int, text: str, use_ml: bool) -> Optional[Finding]:
    probs = classifier.predict_proba(text) if use_ml else {}
    scored = []
    for cat in CATEGORIES:
        rule_score, reasons = score_category(cat, text)
        p = probs.get(cat.name, 0.0)
        if rule_score > 0:
            final = 1.0 - (1.0 - rule_score) * (1.0 - ML_WEIGHT * p)
            source = "rules+ml" if p >= 0.3 else "rules"
        elif p >= ML_ONLY_MIN_PROB:
            final, source = ML_ONLY_SCORE + 0.1 * (p - ML_ONLY_MIN_PROB), "ml"
            reasons = [f"Language resembles known {cat.name.lower()} clauses (model confidence {p:.0%})"]
        else:
            continue
        if final > 0 and _MUTUAL.search(text):
            final *= 0.85
            reasons = reasons + ["Obligation is mutual (slightly lowers risk)"]
        scored.append((final, cat.name, reasons, source))

    if not scored:
        return None
    scored.sort(key=lambda s: s[0], reverse=True)
    score, name, reasons, source = scored[0]
    level = level_for(score)
    if level is None:
        return None
    also = [s[1] for s in scored[1:] if level_for(s[0])]
    return Finding(
        index=index,
        text=text,
        category=name,
        level=level,
        score=round(score, 3),
        explanation="; ".join(reasons),
        recommendation=CATEGORY_BY_NAME[name].advice,
        source=source,
        also=also,
    )


def analyze_contract(text: str, use_ml: bool = True) -> ContractReport:
    clauses_text = segment_clauses(text)
    clauses: List[Tuple[str, Optional[Finding]]] = []
    findings: List[Finding] = []
    for i, clause in enumerate(clauses_text):
        finding = _analyze_clause(i, clause, use_ml)
        clauses.append((clause, finding))
        if finding:
            findings.append(finding)

    # Severity points saturate smoothly: ~4 High clauses ~ 63, one High + a few Low ~ 25.
    points = sum(POINTS[f.level] for f in findings)
    overall = int(round(100 * (1.0 - math.exp(-points / 40))))
    overall_level = "High" if overall >= 60 else "Medium" if overall >= 30 else "Low"

    return ContractReport(
        clauses=clauses,
        findings=sorted(findings, key=lambda f: (-LEVEL_ORDER[f.level], -f.score, f.index)),
        overall_score=overall,
        overall_level=overall_level,
        category_counts=dict(Counter(f.category for f in findings)),
        level_counts={lv: sum(1 for f in findings if f.level == lv) for lv in ("High", "Medium", "Low")},
    )
