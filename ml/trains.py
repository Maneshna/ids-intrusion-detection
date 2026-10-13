import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier

def train_random_forest(X_train, y_train):
    class_weights = compute_class_weight('balanced',
                                          classes=np.unique(y_train),
                                          y=y_train)
    class_weight_dict = {0: class_weights[0], 1: class_weights[1]}

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        class_weight=class_weight_dict,
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)
    pickle.dump(model, open('../results/random_forest_model.pkl', 'wb'))
    print("Random Forest trained and saved.")
    return model

def train_xgboost(X_train, y_train):
    scale_pos = (y_train == 0).sum() / (y_train == 1).sum()

    model = XGBClassifier(
        n_estimators=100,
        max_depth=7,
        learning_rate=0.1,
        scale_pos_weight=scale_pos,
        tree_method='hist',
        device='cuda',
        random_state=42,
        eval_metric='logloss'
    )
    model.fit(X_train, y_train)
    pickle.dump(model, open('../results/xgboost_tuned_model.pkl', 'wb'))
    print("XGBoost trained and saved.")
    return model

def train_isolation_forest(X_train, y_train):
    X_benign = X_train[y_train == 0]

    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_benign)
    pickle.dump(model, open('../results/isolation_forest_model.pkl', 'wb'))
    print("Isolation Forest trained and saved.")
    return model

if __name__ == "__main__":
    X_train = pd.read_csv('../data/X_train.csv')
    y_train = pd.read_csv('../data/y_train.csv').squeeze()

    train_random_forest(X_train, y_train)
    train_xgboost(X_train, y_train)
    train_isolation_forest(X_train, y_train)
    print("All models trained.")