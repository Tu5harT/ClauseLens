# ClauseLens (Contract Risk Highlighter)

An NLP system that reads a contract (PDF / DOCX / TXT / pasted text), highlights risky clauses,
classifies each by **risk type**, assigns a **risk level** (High / Medium / Low) and explains *why*,
with a suggested negotiation action. Includes an overall 0-100 risk score and CSV/JSON export.

## Features

- Accounts (sign up / sign in); every analysed document is saved per account and can be reopened or deleted.
- Risk heat-strip: one block per clause, so you see where the danger sits in the document.
- Fairer-wording suggestions for each risk type, plus a downloadable negotiation brief.
- Overall score from severity points (High=10, Medium=4, Low=1, smoothly capped at 100).

Data lives in SQLite at `data/app.db` (set `DATA_DIR` to a persistent volume when deploying; ephemeral hosts lose it).
Contract text is stored unencrypted, so don't host this publicly for sensitive documents without adding encryption.

## How it works

```
Upload -> text extraction (pypdf / python-docx)
       -> clause segmentation (headings dropped, sentence-level units)
       -> hybrid scoring per clause
            1. Rule engine: weighted regex lexicon, 11 risk categories (explainable)
            2. ML classifier: TF-IDF (word + char n-grams) + Logistic Regression
       -> noisy-OR score fusion -> level (High >= 0.60, Medium >= 0.35, Low >= 0.20)
       -> highlighted document, findings table, summary, export
```

Categories: Liability & Indemnification, Payment Terms, Termination, Auto-Renewal, Confidentiality,
Intellectual Property, Non-Compete & Exclusivity, Dispute Resolution, Warranty Disclaimer,
Unilateral Changes, Data Privacy.

The rule engine drives the score and the explanation. The classifier (trained on
`data/seed_clauses.csv`, 73 labelled clauses) nudges rule scores and can flag clauses the
rules miss (marked "ml"). Mutual obligations ("either party") slightly lower risk.

## Run locally

```bash
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -r requirements.txt
python train.py          # optional: trains + saves the model (auto-trains on first run otherwise)
streamlit run app.py
python -m pytest         # tests
```

Try it with `samples/sample_contract.txt` (also the default in the sidebar).

## Deploy

**Streamlit Community Cloud (free):** push this folder to GitHub -> share.streamlit.io -> New app ->
select the repo, main file `app.py`. Done.

**Docker (Render, Railway, Fly.io, Azure, AWS...):**
```bash
docker build -t contract-risk .
docker run -p 8501:8501 contract-risk
```
The container honours `$PORT`, so it works on platforms that inject one.

**Hugging Face Spaces:** create a Docker Space, push this repo, and set `PORT=7860` (or use
`app_port: 8501` in the Space's README metadata).

## Project layout

```
app.py                  Streamlit UI
risk_engine/
  segmenter.py          clause segmentation
  rules.py              categories, regex rules, advice (edit this to extend coverage)
  classifier.py         TF-IDF + LogReg model
  analyzer.py           score fusion, report objects
data/seed_clauses.csv   labelled training clauses
train.py                trains model + prints cross-validated accuracy
tests/                  pytest suite
```

## Limitations (good to mention in your report)

- Cross-validated accuracy of the classifier on the small seed set is ~0.48 over 12 classes, so it is a
  supporting signal; precision comes mainly from the rules. Adding more labelled clauses
  (e.g. the CUAD dataset) to `data/seed_clauses.csv` and re-running `train.py` is the main upgrade path.
- English only; scanned PDFs need OCR first.
- Automated screening aid, **not legal advice**.
