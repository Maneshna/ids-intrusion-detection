"""Flask server: serves the frontend, the result images, and the /api/predict endpoint.
Run from the PROJECT ROOT:  python backend/app.py
"""
import io, os, sys
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # lets us `import ml.predict`
FRONTEND, RESULTS = ROOT / "frontend", ROOT / "results"

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024   # 50 MB upload limit


def run_model(df: pd.DataFrame):
    """Return (is_attack[bool array], attack_prob[float array], anomaly[bool array]).

    >>> EDIT THIS ONE FUNCTION to match ml/predict.py <<<
    Expected contract:
        ml.predict.predict(df) -> (labels, probs)
            labels: 1 = attack, 0 = benign
            probs : probability of the attack class (0..1)
        ml.predict.anomaly_flags(df) -> bool array   (optional)
    Set DEMO=1 to get random results while you wire this up.
    """
    if os.environ.get("DEMO") == "1":
        rng = np.random.default_rng(0)
        p = rng.random(len(df)) ** 4
        return p > 0.5, p, rng.random(len(df)) < 0.05

    from ml.predict import predict            # <- your file
    labels, probs = predict(df)
    labels, probs = np.asarray(labels).astype(bool), np.asarray(probs, dtype=float)
    try:
        from ml.predict import anomaly_flags  # optional
        anomaly = np.asarray(anomaly_flags(df)).astype(bool)
    except ImportError:
        anomaly = np.zeros(len(df), dtype=bool)
    return labels, probs, anomaly


@app.post("/api/predict")
def api_predict():
    f = request.files.get("file")
    if f is None or not f.filename.lower().endswith(".csv"):
        return jsonify(error="Please upload a file that ends in .csv."), 400
    try:
        df = pd.read_csv(io.BytesIO(f.read()))
    except Exception:
        return jsonify(error="Could not parse the file as CSV."), 400
    if df.empty:
        return jsonify(error="The CSV has no rows."), 400
    df = df.drop(columns=[c for c in df.columns if c.strip().lower() in ("label", "class")], errors="ignore")
    try:
        is_atk, p, anomaly = run_model(df)
    except Exception as e:
        app.logger.exception("model failed")
        return jsonify(error=f"Model error: {e}. Check that the columns match the training data."), 422

    conf = np.where(is_atk, p, 1 - p)      # confidence in the predicted label
    rows = [{"i": i + 1, "atk": bool(a), "c": float(c), "an": bool(n)}
            for i, (a, c, n) in enumerate(zip(is_atk, conf, anomaly))]
    return jsonify(total=len(rows), attacks=int(is_atk.sum()), rows=rows)


@app.get("/results/<path:name>")
def results(name):
    return send_from_directory(RESULTS, name)


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:name>")
def static_files(name):
    return send_from_directory(FRONTEND, name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
