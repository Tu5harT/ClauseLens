import fitz

from risk_engine import analyze_contract, pdf_view
from risk_engine.fixer import apply_fixes

SAMPLE = open("samples/sample_contract.txt", encoding="utf8").read()


def make_pdf(text: str) -> bytes:
    doc = fitz.open()
    lines = text.split("\n")
    for start in range(0, len(lines), 28):  # hard-wrapped, multi-page like a real PDF
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(50, 50, 545, 790), "\n".join(lines[start : start + 28]), fontsize=10)
    return doc.tobytes()


def test_pdf_highlights_land_on_pages():
    data = make_pdf(SAMPLE)
    report = analyze_contract(pdf_view.extract_text(data))
    pngs, annotated, pages = pdf_view.annotate(data, report)
    assert len(pngs) >= 2 and pngs[0][:4] == b"\x89PNG"
    flagged = len(report.findings)
    assert flagged >= 10 and len(pages) >= flagged - 1  # nearly every finding located
    annots = sum(1 for p in fitz.open(stream=annotated, filetype="pdf") for _ in p.annots())
    assert annots >= flagged


def test_apply_fixes_replaces_wrapped_clause_and_lowers_risk():
    text = "1. Fees\nAll fees are non-refundable and\npayable immediately upon receipt.\n2. General\nNotices must be in writing."
    report = analyze_contract(text)
    idx = [f.index for f in report.findings][0]
    revised, missed = apply_fixes(text, [c for c, _ in report.clauses], {idx: "Invoices are payable within 30 days."})
    assert missed == [] and "non-refundable" not in revised and "Notices must be in writing." in revised
    assert analyze_contract(revised).overall_score < report.overall_score


def test_apply_fixes_reports_missing_clause():
    _, missed = apply_fixes("abc def", ["not present here"], {0: "x"})
    assert missed == [0]
