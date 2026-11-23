"""
SentinelX Alert Management APIs
Handles investigation queuing, assignment, triage, and status updates with full audit trails.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from backend.app.models.schemas import AlertUpdateStatus, AlertAssign
from backend.app.database.connection import get_collection
from backend.app.security.authentication import get_current_user

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts Management"])

@router.get("", response_model=Dict[str, Any])
def list_alerts(
    status_filter: Optional[str] = Query(None, description="Filter: OPEN, UNDER_REVIEW, RESOLVED, DISMISSED"),
    severity: Optional[str] = Query(None, description="Filter: HIGH, CRITICAL"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned analyst"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    alerts_col = get_collection("fraud_alerts")
    preds_col = get_collection("predictions")
    txns_col = get_collection("transactions")
    
    query: Dict[str, Any] = {}
    if status_filter and isinstance(status_filter, str):
        query["status"] = status_filter.upper()
    if severity and isinstance(severity, str):
        query["severity"] = severity.upper()
    if assigned_to and isinstance(assigned_to, str):
        query["assigned_to"] = assigned_to
        
    limit_val = limit if isinstance(limit, int) else 50
    skip_val = skip if isinstance(skip, int) else 0
        
    total = alerts_col.count_documents(query)
    raw_alerts = list(alerts_col.find(query, {"_id": 0}).sort("created_at", -1).skip(skip_val).limit(limit_val))
    
    # Enrich with transaction & prediction summary
    enriched = []
    for a in raw_alerts:
        txn_id = a.get("transaction_id")
        txn = txns_col.find_one({"transaction_id": txn_id}, {"_id": 0})
        pred = preds_col.find_one({"transaction_id": txn_id}, {"_id": 0})
        a["transaction"] = txn
        a["prediction"] = pred
        enriched.append(a)
        
    return {
        "total": total,
        "returned": len(enriched),
        "skip": skip,
        "limit": limit,
        "alerts": enriched
    }

@router.get("/{alert_id}", response_model=Dict[str, Any])
def get_alert_details(alert_id: str, current_user: dict = Depends(get_current_user)):
    alerts_col = get_collection("fraud_alerts")
    txns_col = get_collection("transactions")
    preds_col = get_collection("predictions")
    inv_col = get_collection("investigations")
    
    alert = alerts_col.find_one({"alert_id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
        
    txn_id = alert.get("transaction_id")
    txn = txns_col.find_one({"transaction_id": txn_id}, {"_id": 0})
    pred = preds_col.find_one({"transaction_id": txn_id}, {"_id": 0})
    investigations = list(inv_col.find({"alert_id": alert_id}, {"_id": 0}))
    
    return {
        "alert": alert,
        "transaction": txn,
        "prediction": pred,
        "investigations": investigations
    }

@router.patch("/{alert_id}/status", response_model=Dict[str, Any])
def update_alert_status(alert_id: str, payload: AlertUpdateStatus, current_user: dict = Depends(get_current_user)):
    alerts_col = get_collection("fraud_alerts")
    audit_col = get_collection("audit_logs")
    
    existing = alerts_col.find_one({"alert_id": alert_id})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
        
    prev_status = existing.get("status", "OPEN")
    new_status = payload.status.upper()
    analyst_id = payload.analyst_id or current_user.get("user_id", "USR_ANALYST")
    
    alerts_col.update_one(
        {"alert_id": alert_id},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow().isoformat() + "Z"}}
    )
    
    # Audit trail
    audit_col.insert_one({
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "user_id": analyst_id,
        "action": "ALERT_STATUS_UPDATED",
        "resource_id": alert_id,
        "previous_status": prev_status,
        "new_status": new_status,
        "remarks": payload.remarks,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    
    return {
        "status": "UPDATED",
        "alert_id": alert_id,
        "previous_status": prev_status,
        "new_status": new_status
    }

@router.post("/{alert_id}/assign", response_model=Dict[str, Any])
def assign_alert(alert_id: str, payload: AlertAssign, current_user: dict = Depends(get_current_user)):
    alerts_col = get_collection("fraud_alerts")
    audit_col = get_collection("audit_logs")
    
    existing = alerts_col.find_one({"alert_id": alert_id})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
        
    alerts_col.update_one(
        {"alert_id": alert_id},
        {"$set": {"assigned_to": payload.assigned_to, "status": "UNDER_REVIEW"}}
    )
    
    audit_col.insert_one({
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "user_id": payload.analyst_id or current_user.get("user_id"),
        "action": "ALERT_ASSIGNED",
        "resource_id": alert_id,
        "previous_status": existing.get("assigned_to"),
        "new_status": payload.assigned_to,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    
    return {
        "status": "ASSIGNED",
        "alert_id": alert_id,
        "assigned_to": payload.assigned_to
    }
