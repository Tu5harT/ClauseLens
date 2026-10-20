"""Draw docs/workflow.jpg, the ClauseLens workflow diagram."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BG, CARD, LINE, TXT, MUTED, BLUE = "#14171c", "#1b2130", "#3b82f6", "#e6e9ef", "#8b95ad", "#3b82f6"
fig, ax = plt.subplots(figsize=(16, 10), dpi=130)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis("off")


def box(x, y, w, h, title, sub="", edge=LINE, step=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=CARD, ec=edge, lw=1.8))
    ax.text(x + w / 2, y + h * (0.64 if sub else 0.5), title, ha="center", va="center", color=TXT, fontsize=11.5, fontweight="bold")
    if sub:
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", color=MUTED, fontsize=8.6, linespacing=1.35)
    if step:
        ax.add_patch(plt.Circle((x + 0.02, y + h), 0.2, color=BLUE, zorder=5))
        ax.text(x + 0.02, y + h, str(step), ha="center", va="center", color="white", fontsize=9, fontweight="bold", zorder=6)


def arrow(p1, p2, rad=0.0):
    ax.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle="-|>", color="#8fb4ff", lw=1.8, connectionstyle=f"arc3,rad={rad}"))


def route(pts):
    xs, ys = zip(*pts[:-1])
    ax.plot(xs, ys, color="#8fb4ff", lw=1.8, solid_capstyle="round")
    arrow(pts[-2], pts[-1])


ax.text(8, 9.5, "ClauseLens: Contract Risk Highlighter workflow", ha="center", color="white", fontsize=19, fontweight="bold")
ax.text(8, 9.1, "From an uploaded contract to highlighted risks, fixes and a saved report", ha="center", color=MUTED, fontsize=10.5)

# Row 1: getting the text
y1, h = 7.2, 1.3
box(0.4, y1, 3.3, h, "Sign in / Sign up", "salted PBKDF2 passwords\nper-account storage (db.py)", step=1)
box(4.4, y1, 3.3, h, "Input", "upload PDF / DOCX / TXT\npaste text or try a sample", step=2)
box(8.4, y1, 3.3, h, "Text extraction", "PyMuPDF (PDF), python-docx\nplain read (TXT)", step=3)
box(12.4, y1, 3.3, h, "Clause segmentation", "drop headings, rejoin wrapped lines\none sentence = one clause", step=4)
for a, b in [(3.7, 4.4), (7.7, 8.4), (11.7, 12.4)]:
    arrow((a, y1 + h / 2), (b, y1 + h / 2))

# Row 2: scoring
y2 = 4.0
box(0.4, y2 + 1.05, 3.6, 1.2, "Rule engine", "11 categories, weighted regex\nnoisy-OR score + reasons", edge="#22c55e")
box(0.4, y2 - 0.45, 3.6, 1.2, "ML classifier", "TF-IDF + Logistic Regression\ntrained on 73 labelled clauses", edge="#22c55e")
box(5.0, y2 + 0.25, 3.0, 1.5, "Score fusion", "rule + 0.3 x ML probability\nmutual clause x 0.85", step=5)
box(8.9, y2 + 0.25, 3.0, 1.5, "Level & category", "High >= 0.60\nMedium >= 0.35, Low >= 0.20", step=6)
box(12.4, y2 + 0.25, 3.3, 1.5, "Overall score 0-100", "points: High 10, Med 4, Low 1\n100 x (1 - e^(-points/40))", step=7)
route([(14.05, y1), (14.05, 6.7), (2.2, 6.7), (2.2, y2 + 2.25)])
arrow((4.0, y2 + 1.65), (5.0, y2 + 1.2))
arrow((4.0, y2 + 0.15), (5.0, y2 + 0.8))
arrow((8.0, y2 + 1.0), (8.9, y2 + 1.0))
arrow((11.9, y2 + 1.0), (12.4, y2 + 1.0))
ax.text(8.2, 6.82, "every clause is then scored two ways", ha="center", color=MUTED, fontsize=8.5, style="italic")
ax.text(8.2, 3.22, "results feed the viewer, the fixer and the database", ha="center", color=MUTED, fontsize=8.5, style="italic")

# Row 3: outputs
y3 = 0.9
box(0.4, y3, 3.6, 1.5, "PDF highlighting", "find clause words on the page\nhighlight annotations + margin badges", step=8)
box(4.6, y3, 3.6, 1.5, "Findings & fixes", "reason, advice, editable fairer wording\napply one or all fixes", step=9)
box(8.8, y3, 3.2, 1.5, "Re-score", "re-run steps 4-7 on revised text\nbefore -> after gauge", step=10)
box(12.6, y3, 3.1, 1.5, "Save & export", "SQLite per account, reopen later\nhighlighted PDF, revised .docx/.txt", step=11)
route([(14.05, y2 + 0.25), (14.05, 3.1), (2.2, 3.1), (2.2, y3 + 1.5)])
arrow((4.0, y3 + 0.75), (4.6, y3 + 0.75))
arrow((8.2, y3 + 0.75), (8.8, y3 + 0.75))
arrow((12.0, y3 + 0.75), (12.6, y3 + 0.75))
ax.text(8, 0.35, "Automated screening aid, not legal advice", ha="center", color=MUTED, fontsize=9)

fig.savefig("docs/workflow.jpg", format="jpg", facecolor=BG, pil_kwargs={"quality": 92})
