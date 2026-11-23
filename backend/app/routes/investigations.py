"""
SentinelX Fraud Investigation Centre APIs
Enables analysts to document decisions (CONFIRMED_FRAUD, LEGITIMATE_TRANSACTION),
add case notes, and resolve escalated alerts.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from backend.app.models.schemas import InvestigationCreate, InvestigationOut
from backend.app.database.connection import get_collection
from backend.app.security.authentication import get_current_user

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigations"])

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_investigation(payload: InvestigationCreate, current_user: dict = Depends(get_current_user)):
    inv_col = get_collection("investigations")
    alerts_col = get_collection("fraud_alerts")
    cust_col = get_collection("customers")
    txns_col = get_collection("transactions")
    audit_col = get_collection("audit_logs")
    
    alert = alerts_col.find_one({"alert_id": payload.alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {payload.alert_id} not found.")
        
    inv_id = f"INV_{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    inv_doc = {
        "investigation_id": inv_id,
        "alert_id": payload.alert_id,
        "analyst_id": payload.analyst_id or current_user.get("user_id", "USR_101"),
        "decision": payload.decision.upper(),
        "remarks": payload.remarks,
        "reviewed_at": timestamp
    }
    inv_col.insert_one(inv_doc.copy())
    
    # Auto-resolve alert
    alerts_col.update_one(
        {"alert_id": payload.alert_id},
        {"$set": {"status": "RESOLVED", "resolved_decision": payload.decision.upper(), "resolved_at": timestamp}}
    )
    
    # If confirmed fraud, update customer risk profile
    if payload.decision.upper() == "CONFIRMED_FRAUD":
        txn_id = alert.get("transaction_id")
        txn = txns_col.find_one({"transaction_id": txn_id})
        if txn:
            orig_acc = txn.get("origin_account")
            cust_col.update_one(
                {"account_id": orig_acc},
                {"$inc": {"risk_history.confirmed_fraud_cases": 1}}
            )
            
    # Audit log
    audit_col.insert_one({
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "user_id": payload.analyst_id or current_user.get("user_id"),
        "action": "INVESTIGATION_COMPLETED",
        "resource_id": inv_id,
        "alert_id": payload.alert_id,
        "decision": payload.decision.upper(),
        "timestamp": timestamp
    })
    
    return {
        "status": "RECORDED",
        "investigation_id": inv_id,
        "investigation": inv_doc
    }

@router.get("", response_model=Dict[str, Any])
def list_investigations(
    decision: Optional[str] = Query(None, description="Filter: CONFIRMED_FRAUD, LEGITIMATE_TRANSACTION"),
    analyst_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    inv_col = get_collection("investigations")
    query = {}
    if decision:
        query["decision"] = decision.upper()
    if analyst_id:
        query["analyst_id"] = analyst_id
        
    records = list(inv_col.find(query, {"_id": 0}).sort("reviewed_at", -1).limit(limit))
    return {
        "total": len(records),
        "investigations": records
    }

@router.patch("/{investigation_id}", response_model=Dict[str, Any])
def update_investigation(investigation_id: str, payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    inv_col = get_collection("investigations")
    audit_col = get_collection("audit_logs")
    
    res = inv_col.update_one(
        {"investigation_id": investigation_id},
        {"$set": payload}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Investigation record not found.")
        
    audit_col.insert_one({
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "user_id": current_user.get("user_id"),
        "action": "INVESTIGATION_UPDATED",
        "resource_id": investigation_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    
    return {"status": "UPDATED", "investigation_id": investigation_id}
