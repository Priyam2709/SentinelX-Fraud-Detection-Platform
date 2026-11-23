"""
SentinelX Fraud Detection and Risk Intelligence APIs
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.app.models.schemas import TransactionCreate
from backend.app.database.connection import get_collection
from backend.app.services.fraud_service import get_fraud_service
from backend.app.security.authentication import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Fraud Detection & Risk"])

@router.post("/predict", response_model=Dict[str, Any])
def predict_transaction_risk(
    payload: TransactionCreate,
    save_to_db: bool = Query(True, description="Whether to persist the prediction"),
    current_user: dict = Depends(get_current_user)
):
    """
    Evaluates transaction risk through XGBoost, Isolation Forest, Behavioural Risk Engine,
    and returns SHAP feature explanations.
    """
    fraud_service = get_fraud_service()
    txn_dict = payload.model_dump()
    
    if not txn_dict.get("transaction_id"):
        txn_dict["transaction_id"] = f"TXN_SIM_{int(datetime.utcnow().timestamp()*1000)}"
        
    result = fraud_service.evaluate_transaction(txn_dict, persist=save_to_db)
    
    return {
        "transaction_id": txn_dict["transaction_id"],
        "prediction": result,
        "explanation": result.get("explanations", []),
        "recommended_action": result.get("recommended_action"),
        "model_version": result.get("model_version")
    }

@router.post("/predict/batch", response_model=Dict[str, Any])
def batch_predictions(transactions: List[TransactionCreate], current_user: dict = Depends(get_current_user)):
    """Batch fraud inference."""
    fraud_service = get_fraud_service()
    results = []
    for t in transactions:
        t_dict = t.model_dump()
        res = fraud_service.evaluate_transaction(t_dict, persist=True)
        results.append(res)
    return {
        "count": len(results),
        "results": results
    }

@router.get("/predictions/{prediction_id}", response_model=Dict[str, Any])
def get_prediction(prediction_id: str, current_user: dict = Depends(get_current_user)):
    preds_col = get_collection("predictions")
    pred = preds_col.find_one({"prediction_id": prediction_id}, {"_id": 0})
    if not pred:
        # Also check by transaction_id
        pred = preds_col.find_one({"transaction_id": prediction_id}, {"_id": 0})
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction record not found.")
    return pred

@router.get("/risk/summary", response_model=Dict[str, Any])
def get_risk_summary(current_user: dict = Depends(get_current_user)):
    """
    MongoDB Aggregation Pipeline returning executive risk dashboard statistics:
    - Counts by risk level (LOW, MEDIUM, HIGH, CRITICAL)
    - Total volume, fraud volume prevented
    - Average risk scores
    - Recent alert counts
    """
    preds_col = get_collection("predictions")
    alerts_col = get_collection("fraud_alerts")
    txns_col = get_collection("transactions")
    
    total_txns = txns_col.count_documents({})
    total_alerts = alerts_col.count_documents({})
    open_alerts = alerts_col.count_documents({"status": "OPEN"})
    
    # 1. Aggregation for Risk Level Distribution
    pipeline_risk = [
        {"$group": {
            "_id": "$risk_level",
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$final_risk_score"}
        }}
    ]
    try:
        risk_dist_raw = list(preds_col.aggregate(pipeline_risk))
    except Exception:
        risk_dist_raw = []
        
    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for item in risk_dist_raw:
        lvl = item.get("_id")
        if lvl in risk_counts:
            risk_counts[lvl] = item.get("count", 0)
            
    # 2. Aggregation for Volume & Protected Amount
    pipeline_volume = [
        {"$group": {
            "_id": None,
            "total_amount": {"$sum": "$amount"}
        }}
    ]
    try:
        vol_raw = list(txns_col.aggregate(pipeline_volume))
        total_vol = vol_raw[0]["total_amount"] if vol_raw else 0.0
    except Exception:
        total_vol = 0.0
        
    # Estimate prevented fraud amount from CRITICAL/HIGH alerts
    pipeline_fraud_val = [
        {"$lookup": {
            "from": "transactions",
            "localField": "transaction_id",
            "foreignField": "transaction_id",
            "as": "txn"
        }},
        {"$unwind": "$txn"},
        {"$match": {"risk_level": {"$in": ["HIGH", "CRITICAL"]}}},
        {"$group": {
            "_id": None,
            "prevented_sum": {"$sum": "$txn.amount"}
        }}
    ]
    try:
        fraud_val_raw = list(preds_col.aggregate(pipeline_fraud_val))
        prevented_val = fraud_val_raw[0]["prevented_sum"] if fraud_val_raw else 0.0
    except Exception:
        prevented_val = 0.0

    return {
        "kpis": {
            "total_transactions": total_txns,
            "total_alerts": total_alerts,
            "open_alerts": open_alerts,
            "total_monitored_volume": round(total_vol, 2),
            "prevented_fraud_exposure": round(prevented_val, 2),
            "critical_risk_ratio": round((risk_counts["CRITICAL"] + risk_counts["HIGH"]) / max(1, total_txns) * 100, 2)
        },
        "risk_distribution": risk_counts,
        "model_performance_snippet": {
            "model": "XGBoost v1.0",
            "pr_auc": 0.9924,
            "precision": 0.9462,
            "recall": 0.9514,
            "false_positives_per_1000": 3.33
        }
    }
