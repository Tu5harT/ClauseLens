"""Train the clause classifier and print a cross-validated accuracy estimate."""
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold

from risk_engine import classifier


def main() -> None:
    df = pd.read_csv(classifier.DATA_PATH, keep_default_na=False)
    min_class = df["label"].value_counts().min()
    cv = StratifiedKFold(n_splits=min(5, min_class), shuffle=True, random_state=0)
    scores = cross_val_score(classifier.build_pipeline(), df["text"], df["label"], cv=cv)
    print(f"{len(df)} clauses, {df['label'].nunique()} classes")
    print(f"Cross-val accuracy: {scores.mean():.2f} +/- {scores.std():.2f}")
    classifier.train()
    print(f"Saved model to {classifier.MODEL_PATH}")


if __name__ == "__main__":
    main()
