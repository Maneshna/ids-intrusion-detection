import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, roc_curve, auc,
    classification_report
)
import os

os.makedirs('../results', exist_ok=True)

def evaluate_model(model_name, y_true, y_pred, y_proba=None):
    print(f"\n{'='*45}")
    print(f"Model: {model_name}")
    print(f"{'='*45}")
    print(f"Accuracy:  {accuracy_score(y_true, y_pred):.4f}")
    print(f"Precision: {precision_score(y_true, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_true, y_pred):.4f}")
    print(f"F1 Score:  {f1_score(y_true, y_pred):.4f}")
    print(f"\n{classification_report(y_true, y_pred)}")

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"TN: {tn}  FP: {fp}  FN: {fn}  TP: {tp}")
    print(f"False Positive Rate: {fp / (fp + tn):.2%}")
    print(f"False Negative Rate: {fn / (fn + tp):.2%}")

    # ROC curve
    if y_proba is not None:
        fpr, tpr, _ = roc_curve(y_true, y_proba)
        roc_auc = auc(fpr, tpr)
        print(f"AUC: {roc_auc:.4f}")

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2,
                 label=f'ROC (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], 'navy', lw=1, linestyle='--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {model_name}')
        plt.legend()
        plt.tight_layout()
        plt.savefig('../results/roc_curve.png', dpi=150)
        plt.close()
        print("ROC curve saved.")

    return {
        'accuracy':  accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred),
        'recall':    recall_score(y_true, y_pred),
        'f1':        f1_score(y_true, y_pred),
    }

if __name__ == "__main__":
    X_test = pd.read_csv('../data/X_test.csv')
    y_test = pd.read_csv('../data/y_test.csv').squeeze()

    xgb   = pickle.load(open('../results/xgboost_tuned_model.pkl', 'rb'))
    rf    = pickle.load(open('../results/random_forest_model.pkl', 'rb'))

    y_pred_xgb  = xgb.predict(X_test)
    y_proba_xgb = xgb.predict_proba(X_test)[:, 1]
    y_pred_rf   = rf.predict(X_test)
    y_proba_rf  = rf.predict_proba(X_test)[:, 1]

    evaluate_model("XGBoost (Tuned)", y_test, y_pred_xgb, y_proba_xgb)
    evaluate_model("Random Forest",   y_test, y_pred_rf,  y_proba_rf)