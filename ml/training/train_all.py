"""
SentinelX End-to-End Training & Calibration Pipeline
Trains:
1. Logistic Regression (Baseline)
2. Random Forest (Non-linear baseline)
3. XGBoost (Production candidate with scale_pos_weight handling)
4. Isolation Forest (Unsupervised anomaly detection layer)

Evaluates on test holdout, computes PR-AUC, ROC-AUC, confusion matrices, and persists models.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ml.data.dataset_generator import generate_synthetic_paysim
from ml.feature_engineering.engineer import prepare_train_test_split, FEATURE_COLUMNS
from ml.evaluation.metrics import evaluate_fraud_model

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def train_sentinelx_pipeline():
    print("=" * 60)
    print(">> SentinelX Fraud Intelligence - Model Training & Calibration")
    print("=" * 60)
    
    # 1. Dataset Generation
    print("Generating PaySim synthetic transactions (12,000 samples)...")
    df = generate_synthetic_paysim(n_samples=12000, fraud_ratio=0.06, random_state=42)
    print(f"Total transactions: {len(df)} | Fraud instances: {df['isFraud'].sum()} ({df['isFraud'].mean()*100:.2f}%)")
    
    # 2. Chronological Train-Test Split & Feature Engineering
    print("Engineering features and performing chronological split...")
    X_train, X_test, y_train, y_test = prepare_train_test_split(df, test_size=0.25, chronological=True)
    print(f"Train samples: {len(X_train)} | Test samples: {len(X_test)}")
    
    # Fit Standard Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler.joblib'))
    
    results = {}
    
    # -------------------------------------------------------------
    # Model 1: Logistic Regression Baseline
    # -------------------------------------------------------------
    print("\n[1/4] Training Logistic Regression Baseline...")
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    lr_prob = lr.predict_proba(X_test_scaled)[:, 1]
    lr_metrics = evaluate_fraud_model(y_test.values, lr_prob)
    results['Logistic Regression'] = lr_metrics
    joblib.dump(lr, os.path.join(MODELS_DIR, 'logistic_regression.joblib'))
    print(f"  -> Precision: {lr_metrics['precision']} | Recall: {lr_metrics['recall']} | PR-AUC: {lr_metrics['pr_auc']}")
    
    # -------------------------------------------------------------
    # Model 2: Random Forest
    # -------------------------------------------------------------
    print("\n[2/4] Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_prob = rf.predict_proba(X_test)[:, 1]
    rf_metrics = evaluate_fraud_model(y_test.values, rf_prob)
    results['Random Forest'] = rf_metrics
    joblib.dump(rf, os.path.join(MODELS_DIR, 'random_forest.joblib'))
    print(f"  -> Precision: {rf_metrics['precision']} | Recall: {rf_metrics['recall']} | PR-AUC: {rf_metrics['pr_auc']}")
    
    # -------------------------------------------------------------
    # Model 3: XGBoost (Production Candidate)
    # -------------------------------------------------------------
    print("\n[3/4] Training Production XGBoost Classifier...")
    # Calculate scale_pos_weight
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos = max(1.0, float(neg_count / pos_count))
    
    xgb = XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.08,
        scale_pos_weight=scale_pos,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='aucpr',
        random_state=42
    )
    xgb.fit(X_train, y_train)
    xgb_prob = xgb.predict_proba(X_test)[:, 1]
    xgb_metrics = evaluate_fraud_model(y_test.values, xgb_prob, threshold=0.5)
    results['XGBoost (Production)'] = xgb_metrics
    joblib.dump(xgb, os.path.join(MODELS_DIR, 'xgboost_model.joblib'))
    print(f"  -> Precision: {xgb_metrics['precision']} | Recall: {xgb_metrics['recall']} | PR-AUC: {xgb_metrics['pr_auc']} | ROC-AUC: {xgb_metrics['roc_auc']}")
    
    # -------------------------------------------------------------
    # Model 4: Unsupervised Isolation Forest (Anomaly Layer)
    # -------------------------------------------------------------
    print("\n[4/4] Training Unsupervised Isolation Forest...")
    # Fit primarily on legitimate transactions so deviations stand out
    X_train_normal = X_train[y_train == 0]
    iso = IsolationForest(n_estimators=120, contamination=0.05, max_samples=0.8, random_state=42, n_jobs=-1)
    iso.fit(X_train_normal)
    joblib.dump(iso, os.path.join(MODELS_DIR, 'isolation_forest.joblib'))
    print("  -> Isolation Forest trained and saved.")
    
    # -------------------------------------------------------------
    # Persist Registry & Metrics
    # -------------------------------------------------------------
    metrics_path = os.path.join(MODELS_DIR, 'model_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "=" * 60)
    print("[OK] SentinelX Model Artifacts and Evaluation Registry Created:")
    for model_name, m in results.items():
        print(f"  - {model_name:22s} | F1: {m['f1_score']:.4f} | PR-AUC: {m['pr_auc']:.4f} | FP/1000: {m['fp_per_1000']}")
    print("=" * 60)
    
    return results

if __name__ == '__main__':
    train_sentinelx_pipeline()
