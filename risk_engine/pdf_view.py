"""Highlight findings directly on the original PDF pages (PyMuPDF)."""
from __future__ import annotations

from typing import Dict, List, Tuple

import fitz  # PyMuPDF

PALETTE = {"High": (1, 0.45, 0.45), "Medium": (1, 0.82, 0.25), "Low": (0.55, 0.88, 0.55)}
BADGE = {"High": (0.78, 0.13, 0.13), "Medium": (0.85, 0.5, 0.0), "Low": (0.18, 0.6, 0.25)}
LOOKAHEAD = 600  # tokens searched past the last match; keeps matching linear on big PDFs
MAX_RENDER_PAGES = 60


def extract_text(data: bytes) -> str:
    with fitz.open(stream=data, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def _find(tokens: List[str], clause: List[str], start: int):
    k = min(4, len(clause))
    for s in range(start, min(len(tokens) - k, start + LOOKAHEAD) + 1):
        if tokens[s : s + k] == clause[:k]:
            return s
    return None


def annotate(data: bytes, report, dpi: int = 110) -> Tuple[List[bytes], bytes, Dict[int, int]]:
    """Return (page PNGs, annotated PDF bytes, {clause index: page number})."""
    doc = fitz.open(stream=data, filetype="pdf")
    words = [(pno, w) for pno, page in enumerate(doc) for w in page.get_text("words")]
    tokens = [w[1][4] for w in words]

    cursor, pages = 0, {}
    for i, (clause, finding) in enumerate(report.clauses):
        ct = clause.split()
        pos = _find(tokens, ct, cursor)
        if pos is None:
            continue
        cursor = pos + len(ct)
        if not finding:
            continue
        lines: Dict[tuple, fitz.Rect] = {}  # merge words into one rect per text line
        for pno, w in words[pos : pos + len(ct)]:
            key = (pno, w[5], w[6])
            lines[key] = lines.get(key, fitz.Rect(w[:4])) | fitz.Rect(w[:4])
        first = True
        for (pno, _, _), rect in lines.items():
            page = doc[pno]
            annot = page.add_highlight_annot(rect)
            annot.set_colors(stroke=PALETTE[finding.level])
            annot.set_info(content=f"#{i + 1} {finding.category} ({finding.level}): {finding.explanation}")
            annot.update()
            if first:  # numbered badge in the margin matches "clause N" in the findings list
                label = str(i + 1)
                badge = fitz.Rect(1, rect.y0, 8 + 5 * len(label), rect.y0 + 10)
                page.draw_rect(badge, color=None, fill=BADGE[finding.level])
                page.insert_text((badge.x0 + 2, badge.y1 - 2), label, fontsize=7, color=(1, 1, 1))
                pages[i] = pno + 1
                first = False

    pngs = [page.get_pixmap(dpi=dpi).tobytes("png") for page in list(doc)[:MAX_RENDER_PAGES]]
    out = doc.tobytes()
    doc.close()
    return pngs, out, pages
