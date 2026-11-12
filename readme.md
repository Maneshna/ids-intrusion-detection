# Network Intrusion Detection System with Explainable ML

A machine learning system that classifies network flows as **attack or benign**, flags **unusual behavior** with an anomaly detector, and **explains every decision** with SHAP. A web dashboard lets a security analyst upload flow data and review the results.

Built on the CICIDS2017 dataset as a final-year major project.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [How It Works](#how-it-works)
3. [Project Structure](#project-structure)
4. [Dataset](#dataset)
5. [Preprocessing](#preprocessing)
6. [Models](#models)
7. [Results](#results)
8. [Explainability](#explainability)
9. [Web Application](#web-application)
10. [Setup and Running](#setup-and-running)
11. [Demo Files](#demo-files)
12. [API Reference](#api-reference)
13. [Limitations](#limitations)
14. [Future Work](#future-work)
15. [Team](#team)

---

## What It Does

Computers on a network constantly exchange data. Each connection is summarized as a **flow**: a row of about 78 numbers such as duration, packet counts, packet sizes, inter-arrival times, and TCP flag counts. Some flows are normal, others are attacks (DDoS floods, port scans, brute-force logins).

This system reads those flow records and, for each one, returns:

- **Prediction:** attack or benign
- **Confidence:** how sure the classifier is
- **Anomaly flag:** whether the flow looks unusual compared to normal traffic
- **Explanation:** which features pushed the decision (via SHAP plots)

The goal is not only accuracy but also trust: analysts are overwhelmed by false alarms, so the system shows why something was flagged and quantifies the cost of false positives.

## How It Works

```
CSV of network flows
        |
        v
React dashboard  -->  Express API  -->  Python scoring (scaler + models)
        ^                                        |
        |                                        v
        +---------- JSON results <---- attack/benign, confidence, anomaly flag
```

Two models answer two different questions:

| Model | Trained on | Question it answers |
|-------|-----------|---------------------|
| XGBoost classifier | Labeled attack and benign flows | Does this look like a known attack? |
| Isolation Forest | Benign flows only | Is this unusual compared to normal traffic? |

XGBoost is accurate on known attack families. Isolation Forest is a second opinion that can flag behavior the classifier was never trained on, at the cost of more false alarms. The dashboard reports both outputs side by side.

## Project Structure

```
ids-intrusion-detection/
├── data/                  # Cleaned dataset and train/test splits
├── ml/                    # Python scripts
│   ├── preprocessing.py   # Cleaning, encoding, scaling, splitting
│   ├── train.py           # Trains Random Forest, XGBoost, Isolation Forest
│   ├── evaluate.py        # Metrics, confusion matrix, ROC curve
│   └── predict.py         # Scoring logic used by the backend
├── notebooks/             # Exploration and experiments (02 to 07)
├── results/               # Saved models, scaler, plots, metrics
├── server/                # Express backend
├── client/                # React frontend
├── demo_samples/          # Sample CSVs for demos
└── README.md
```

## Dataset

**CICIDS2017** from the Canadian Institute for Cybersecurity. Traffic was captured over five days in a lab testbed, and CICFlowMeter extracted flow features from the packets.

Files used:

| File | Contents |
|------|----------|
| Tuesday | Brute force (FTP/SSH-Patator) |
| Wednesday | DoS attacks and Heartbleed |
| Friday afternoon (DDoS) | DDoS |
| Friday afternoon (PortScan) | Port scans |

Files skipped: Monday (benign only), Friday morning (mostly benign), and the Thursday files (web attacks and infiltration, which have few and poorly labeled samples).

## Preprocessing

1. Combined the selected CSV files.
2. Removed rows with missing or infinite values (for example, bytes-per-second for zero-duration flows). Saved as `cicids2017_cleaned.csv`.
3. Stripped leading spaces from column names (the raw dataset has names like `' Label'`).
4. Created a binary target `is_attack` (0 for BENIGN, 1 for any attack). A multi-class label encoder is also saved for future use.
5. Separated the features from the label columns.
6. Applied `StandardScaler`, saved as `results/scaler.pkl`. New data must go through this same scaler before prediction.
7. Split 80/20 with stratification on the target and `random_state=42`.
8. Handled class imbalance at training time with `scale_pos_weight` (XGBoost) and balanced class weights (Random Forest).

## Models

**Random Forest** (baseline): 100 trees, max depth 15, balanced class weights.

**XGBoost** (main classifier): gradient-boosted trees trained with the `hist` method on GPU. Hyperparameters tuned with `RandomizedSearchCV` (10 iterations, 3-fold CV, scored on F1) over depth, learning rate, number of estimators, subsample, and column sample.

**Isolation Forest** (anomaly detector): trained only on benign training flows with `contamination=0.05`, so roughly the most abnormal 5% of flows are flagged. This threshold is a ranking cutoff, not the true attack rate.

Saved artifacts in `results/`:

```
scaler.pkl
label_encoder.pkl
random_forest_model.pkl
xgboost_model.pkl
xgboost_tuned_model.pkl
isolation_forest_model.pkl
```

## Results

Tuned XGBoost on the held-out test set (138,282 flows):

| Metric | Value |
|--------|-------|
| True negatives | 87,879 |
| False positives | 58 |
| False negatives | 10 |
| True positives | 50,335 |
| Accuracy | about 99.95% |
| Precision | about 99.88% |
| Recall | about 99.98% |
| False positive rate | 0.07% |
| False negative rate | 0.02% |
| AUC | about 1.0 |

Train and test scores were compared and showed no overfitting gap.

**Interpreting these numbers:** CICIDS2017 is a clean lab dataset where attack families have very distinctive signatures, so near-perfect scores are expected and should not be read as real-world performance. See [Limitations](#limitations).

**False positive cost analysis:** false positives were converted into analyst workload using illustrative assumptions (5 minutes per alert, 100,000 flows per day, $50 per analyst hour). These are assumptions, not measurements, and are included to show why threshold choice matters.

## Explainability

SHAP (`TreeExplainer`) is computed on a random sample of 1,000 test flows. Outputs saved in `results/`:

- `shap_summary_bar.png`: global feature importance
- `shap_beeswarm.png`: direction and size of each feature's effect
- `shap_force_plot.png`: explanation of a single prediction

SHAP explains the model's behavior, not real-world causation.

## Web Application

The dashboard has three pages:

1. **Dashboard:** summary statistics and the ROC curve.
2. **Predictions:** upload a CSV of flows and view a results table with attack/benign badges, confidence, and anomaly flag, plus pagination and an "attacks only" filter.
3. **Explainability:** the SHAP plots with plain-language captions.

Designed states: empty, loading, success, error (bad file), and no attacks found.

## Setup and Running

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) NVIDIA GPU with CUDA for faster XGBoost training

### 1. Python environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install pandas numpy scikit-learn xgboost shap matplotlib seaborn jupyter
```

### 2. Prepare data and train (skip if `results/` already contains the models)

```bash
cd ml
python preprocessing.py
python train.py
python evaluate.py
```

### 3. Start the backend

```bash
cd server
npm install
npm run dev
```

Runs on `http://localhost:5000`.

### 4. Start the frontend

```bash
cd client
npm install
npm start
```

Runs on `http://localhost:3000`.

## Demo Files

Sample CSVs are in `demo_samples/`, generated from the **test split** (data the models never trained on) using **raw, unscaled** values. Do not upload `X_test.csv`, because it is already scaled and the backend would scale it twice.

| File | Purpose |
|------|---------|
| `demo_mixed_200.csv` | Mix of attacks and benign flows (main demo) |
| `demo_benign_only.csv` | Should produce an all-clear result |
| `demo_<AttackType>.csv` | One file per attack family |
| `demo_stream_500.csv` | Larger file for pagination or the simulated live feed |
| `bad_file.csv` | Triggers the error state |
| `*_ANSWERS.csv` | True labels for checking results. Do not upload. |

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/predict` | Upload a CSV (form field `file`), returns predictions |
| GET | `/api/stats` | Summary metrics from the false positive analysis |
| GET | `/images/<file>` | Serves result plots (ROC curve, SHAP images) |

Example response from `/api/predict`:

```json
{
  "total_flows": 200,
  "attacks_found": 50,
  "benign_found": 150,
  "results": [
    {
      "flow_index": 0,
      "prediction": "attack",
      "confidence": 0.9987,
      "is_anomaly": true,
      "anomaly_score": -0.1243
    }
  ]
}
```

Uploaded CSVs must contain the same flow feature columns as the training data. A `Label` column, if present, is ignored.

## Limitations

- **Lab dataset from 2017.** Real traffic is noisier, includes encrypted and evolving attacks, and shifts over time, so real-world performance would be lower.
- **Partial attack coverage.** Only the attack families in the selected files are covered.
- **Possible data leakage.** The scaler was fit on the full dataset before splitting, and CICIDS2017 contains many near-duplicate flows, so test rows may have close twins in the training set. Both can inflate scores.
- **Random split.** Evaluation does not test generalization across days, attack families, or datasets.
- **Batch, not truly real-time.** The model scores flows in milliseconds, but the application works on uploaded files (or a simulated replay), not live packet capture.
- **Binary classification only.** The system does not yet identify which attack type was detected.
- **Isolation Forest is a weaker signal.** Because of its fixed cutoff it flags some benign flows by design.
- **No adversarial testing.** An attacker could modify traffic to evade the model.

## Future Work

- Split before scaling and remove duplicates, then re-evaluate.
- Test generalization across days and on other datasets such as UNSW-NB15.
- Multi-class attack-type classification.
- Adversarial robustness testing.
- Live capture with CICFlowMeter and a streaming pipeline (queue plus WebSocket alerts).
- A learned fusion of the classifier and anomaly scores.
- Watch the CICFlowMeter output file for new rows using `watchfiles` (successor to `watchgod`), so flows from live capture are scored automatically as they are written, without manual uploads.

## Team

| Name | Role |
|------|------|
| (Madhura) | ML: data preparation |
| (Maneshna) | ML: model training, evaluation, SHAP |
| (Sanchit) | Frontend: CSS HTML |
| (Unnati) | Full-stack: backend API |

## Acknowledgements

- CICIDS2017 dataset: Canadian Institute for Cybersecurity, University of New Brunswick
- scikit-learn, XGBoost, SHAP, Express, React