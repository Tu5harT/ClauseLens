from risk_engine import analyze_contract
from risk_engine.segmenter import segment_clauses

SAMPLE = open("samples/sample_contract.txt", encoding="utf8").read()


def _cats(text):
    return {f.category: f for f in analyze_contract(text).findings}


def test_segmenter_splits_sentences_and_drops_headings():
    clauses = segment_clauses("1. Fees\nAll fees are non-refundable. Invoices are due within 7 days of issue.")
    assert clauses == ["All fees are non-refundable.", "Invoices are due within 7 days of issue."]


def test_auto_renewal_detected_high():
    f = _cats("This Agreement shall automatically renew for successive one-year terms unless notice is given ninety days prior.")
    assert f["Auto-Renewal"].level == "High"


def test_unlimited_liability_detected():
    f = _cats("The Contractor's liability under this Agreement shall be unlimited and covers all losses.")
    assert f["Liability & Indemnification"].level in ("High", "Medium")


def test_non_compete_detected():
    f = _cats("The Employee shall not directly or indirectly compete with the Company for five years after leaving.")
    assert "Non-Compete & Exclusivity" in f


def test_benign_clauses_not_flagged():
    text = (
        "This Agreement constitutes the entire agreement between the parties.\n"
        "The headings in this Agreement are for convenience only and do not affect interpretation.\n"
        "Notices shall be in writing and delivered by registered post to the address stated above."
    )
    assert analyze_contract(text).findings == []


def test_sample_contract_is_high_risk_and_ordered():
    report = analyze_contract(SAMPLE)
    assert report.overall_level == "High"
    assert report.level_counts["High"] >= 8
    assert len(report.category_counts) >= 9
    scores = [(f.level, f.score) for f in report.findings]
    assert scores[0][0] == "High"


def test_rules_only_mode_works():
    report = analyze_contract(SAMPLE, use_ml=False)
    assert report.findings and all(f.source == "rules" for f in report.findings)


def test_hard_wrapped_text_keeps_clauses():
    wrapped = "The Provider may terminate this Agreement\nimmediately and without notice in its sole\ndiscretion. Fees are non-refundable."
    assert any("terminate" in c for c in segment_clauses(wrapped))
    assert segment_clauses("Fees are non-refundable\n\nAll disputes go to binding arbitration") != []


def test_fair_contract_scores_low():
    report = analyze_contract(open("samples/fair_contract.txt", encoding="utf8").read())
    assert report.overall_level == "Low", (report.overall_score, [(f.category, f.level) for f in report.findings])
