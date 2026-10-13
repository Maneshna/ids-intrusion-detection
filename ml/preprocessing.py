import pandas as pd
import numpy as np
import pickle
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

def load_and_clean(path='../data/cicids2017_cleaned.csv'):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.dropna()
    df = df[~df.isin([np.inf, -np.inf]).any(axis=1)]
    print(f"Loaded: {df.shape}")
    print(df['Label'].value_counts())
    return df

def preprocess(df):
    os.makedirs('../results', exist_ok=True)
    os.makedirs('../data', exist_ok=True)

    # Encode labels
    label_encoder = LabelEncoder()
    df['attack_type_encoded'] = label_encoder.fit_transform(df['Label'])
    df['is_attack'] = (df['Label'] != 'BENIGN').astype(int)
    pickle.dump(label_encoder, open('../results/label_encoder.pkl', 'wb'))

    # Features and labels
    X = df.drop(['Label', 'is_attack', 'attack_type_encoded'], axis=1)
    y = df['is_attack']

    # Scale
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
    pickle.dump(scaler, open('../results/scaler.pkl', 'wb'))

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # Save
    X_train.to_csv('../data/X_train.csv', index=False)
    X_test.to_csv('../data/X_test.csv', index=False)
    pd.DataFrame({'y': y_train}).to_csv('../data/y_train.csv', index=False)
    pd.DataFrame({'y': y_test}).to_csv('../data/y_test.csv', index=False)

    print(f"Train: {X_train.shape}, Test: {X_test.shape}")
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    df = load_and_clean()
    preprocess(df)
    print("Preprocessing done.")