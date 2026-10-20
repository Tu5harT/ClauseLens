"""Light-weight ML component: TF-IDF + Logistic Regression over seed clauses.

It complements the rule engine: it can recognise risky clauses phrased in ways
the regex lexicon does not anticipate, and its probability nudges rule scores.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_union

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "seed_clauses.csv"
MODEL_PATH = ROOT / "model" / "clause_classifier.joblib"
NEUTRAL_LABEL = "None"


def build_pipeline() -> Pipeline:
    features = make_union(
        TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english"),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True),
    )
    return Pipeline(
        [
            ("features", features),
            ("clf", LogisticRegression(max_iter=3000, C=30.0, class_weight="balanced")),
        ]
    )


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> Pipeline:
    df = pd.read_csv(data_path, keep_default_na=False)
    pipe = build_pipeline().fit(df["text"], df["label"])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_path)
    return pipe


_pipeline: Optional[Pipeline] = None


def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        if MODEL_PATH.exists():
            try:
                _pipeline = joblib.load(MODEL_PATH)
            except Exception:  # version mismatch etc. -> retrain
                _pipeline = train()
        else:
            _pipeline = train()
    return _pipeline


def predict_proba(text: str) -> Dict[str, float]:
    pipe = get_pipeline()
    probs = pipe.predict_proba([text])[0]
    return {label: float(p) for label, p in zip(pipe.classes_, probs)}
