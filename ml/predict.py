"""Model scoring used by backend/app.py.

Contract expected by app.py:
    predict(df)       -> (labels, probs)   labels: 1 = attack, 0 = benign
                                           probs : attack probability (0..1)
    anomaly_flags(df) -> bool array        True = flagged unusual by Isolation Forest
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent      # .../ml
ROOT = HERE.parent                          # project root


def find_model(name):
    """Look in common folders so this works no matter where the server starts."""
    candidates = [
        ROOT / 'results' / name,
        ROOT / 'models' / name,
        ROOT / 'backend' / 'models' / name,
        HERE / 'models' / name,
        HERE / name,
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"{name} not found. Looked in: {[str(c) for c in candidates]}"
    )


# Load models once, when the server starts
scaler     = pickle.load(open(find_model('scaler.pkl'), 'rb'))
xgb_model  = pickle.load(open(find_model('xgboost_tuned_model.pkl'), 'rb'))
iso_forest = pickle.load(open(find_model('isolation_forest_model.pkl'), 'rb'))

# Run XGBoost on CPU (removes the GPU/CPU warning, works on any server)
xgb_model.set_params(device='cpu')


def _prepare(df: pd.DataFrame) -> np.ndarray:
    """Align columns to what the scaler was trained on, clean values, scale."""
    df = df.copy()
    df.columns = df.columns.str.strip()

    if 'Label' in df.columns:
        df = df.drop(columns=['Label'])

    # Match column names and order to the training data
    mapping = {c.strip(): c for c in scaler.feature_names_in_}
    df = df.rename(columns=lambda c: mapping.get(c.strip(), c))

    missing = [c for c in scaler.feature_names_in_ if c not in df.columns]
    if missing:
        raise ValueError(
            f"{len(missing)} required column(s) missing, e.g. {missing[:5]}"
        )
    df = df[list(scaler.feature_names_in_)]

    # Replace values the models cannot handle
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    return scaler.transform(df)


def predict(df: pd.DataFrame):
    X = _prepare(df)
    probs = xgb_model.predict_proba(X)[:, 1]
    labels = (probs >= 0.5).astype(int)
    return labels, probs


def anomaly_flags(df: pd.DataFrame):
    X = _prepare(df)
    return iso_forest.predict(X) == -1      # -1 means anomaly