"""
SentinelX Model Evaluation and Benchmarking Suite
Calculates rigorous metrics designed specifically for extreme class-imbalance fraud scenarios:
- Precision, Recall, F1
- PR-AUC (Precision-Recall Area Under Curve - the gold standard for fraud)
- ROC-AUC
- Confusion Matrix (TN, FP, FN, TP)
- False Positive Rate per 1,000 transactions (Operational cost metric)
- Cost-calibrated threshold analysis
"""

import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    precision_recall_curve, roc_auc_score, auc,
    confusion_matrix, roc_curve
)
from typing import Dict, Any

def evaluate_fraud_model(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
    """
    Evaluates predictions against true labels and returns comprehensive fraud metrics.
    """
    y_pred = (y_prob >= threshold).astype(int)
    
    # 1. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    # 2. Precision, Recall, F1
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    # 3. ROC-AUC and PR-AUC
    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc_auc = 0.5
        
    try:
        p_curve, r_curve, _ = precision_recall_curve(y_true, y_prob)
        pr_auc = float(auc(r_curve, p_curve))
    except Exception:
        pr_auc = 0.0
        
    # 4. False Positives per 1,000 transactions (Crucial banking metric)
    total_txns = len(y_true)
    fp_per_1000 = float((fp / total_txns) * 1000) if total_txns > 0 else 0.0
    
    # 5. Optimal Threshold search (Maximizing F1 or Precision at Recall >= 0.85)
    best_thresh = threshold
    best_f1 = f1
    for t in np.linspace(0.1, 0.9, 17):
        pred_t = (y_prob >= t).astype(int)
        f1_t = f1_score(y_true, pred_t, zero_division=0)
        if f1_t > best_f1:
            best_f1 = float(f1_t)
            best_thresh = float(t)
            
    return {
        'threshold': float(threshold),
        'optimal_threshold': float(best_thresh),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1_score': round(f1, 4),
        'roc_auc': round(roc_auc, 4),
        'pr_auc': round(pr_auc, 4),
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        },
        'fp_per_1000': round(fp_per_1000, 2),
        'total_evaluated': int(total_txns),
        'fraud_count': int(np.sum(y_true))
    }
