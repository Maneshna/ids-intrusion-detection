import pandas as pd
import numpy as np
import pickle

# Load models once (imported by backend)
scaler     = pickle.load(open('../results/scaler.pkl', 'rb'))
xgb_model  = pickle.load(open('../results/xgboost_tuned_model.pkl', 'rb'))
iso_forest = pickle.load(open('../results/isolation_forest_model.pkl', 'rb'))

def predict_flows(df: pd.DataFrame):
    """
    Takes a DataFrame of raw network flows,
    returns predictions for each flow.
    """
    # Strip column spaces
    df.columns = df.columns.str.strip()

    # Drop label if present
    if 'Label' in df.columns:
        df = df.drop(columns=['Label'])

    # Scale
    features_scaled = scaler.transform(df)

    # Predictions
    predictions    = xgb_model.predict(features_scaled)
    probabilities  = xgb_model.predict_proba(features_scaled)[:, 1]
    anomaly_scores = iso_forest.decision_function(features_scaled)
    anomaly_preds  = iso_forest.predict(features_scaled)

    results = []
    for i in range(len(predictions)):
        results.append({
            "flow_index":    i,
            "prediction":    "attack" if predictions[i] == 1 else "benign",
            "confidence":    round(float(probabilities[i]), 4),
            "is_anomaly":    bool(anomaly_preds[i] == -1),
            "anomaly_score": round(float(anomaly_scores[i]), 4),
        })

    return results