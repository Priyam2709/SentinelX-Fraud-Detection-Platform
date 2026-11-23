"""
SentinelX Transaction API Routes
Handles transaction submission, bulk ingestion, querying with compound filters,
and transaction inspection.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from backend.app.models.schemas import TransactionCreate, TransactionOut
from backend.app.database.connection import get_collection
from backend.app.services.fraud_service import get_fraud_service
from backend.app.security.authentication import get_current_user

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def submit_transaction(payload: TransactionCreate, current_user: dict = Depends(get_current_user)):
    """
    Submits a new financial transaction, evaluates it across the 3-layer risk engine,
    persists records, and returns the real-time risk decision.
    """
    fraud_service = get_fraud_service()
    txn_dict = payload.model_dump()
    
    # Generate unique ID if not provided
    if not txn_dict.get("transaction_id"):
        txn_dict["transaction_id"] = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        
    if not txn_dict.get("created_at"):
        txn_dict["created_at"] = datetime.utcnow().isoformat() + "Z"
        
    # Check idempotency
    txns_col = get_collection("transactions")
    existing = txns_col.find_one({"transaction_id": txn_dict["transaction_id"]})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transaction with ID {txn_dict['transaction_id']} already exists."
        )
        
    txns_col.insert_one(txn_dict.copy())
    
    # Process through fraud evaluation engine
    eval_result = fraud_service.evaluate_transaction(txn_dict, persist=True)
    
    return {
        "status": "PROCESSED",
        "transaction_id": txn_dict["transaction_id"],
        "transaction": txn_dict,
        "risk_evaluation": eval_result
    }

@router.post("/bulk", response_model=Dict[str, Any])
def bulk_transaction_ingestion(transactions: List[TransactionCreate], current_user: dict = Depends(get_current_user)):
    """
    Ingests and scores transactions in bulk.
    """
    fraud_service = get_fraud_service()
    txns_col = get_collection("transactions")
    
    created_txns = []
    evaluations = []
    
    for txn in transactions:
        t_dict = txn.model_dump()
        if not t_dict.get("transaction_id"):
            t_dict["transaction_id"] = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        if not t_dict.get("created_at"):
            t_dict["created_at"] = datetime.utcnow().isoformat() + "Z"
            
        txns_col.insert_one(t_dict.copy())
        eval_res = fraud_service.evaluate_transaction(t_dict, persist=True)
        created_txns.append(t_dict["transaction_id"])
        evaluations.append(eval_res)
        
    return {
        "status": "BATCH_PROCESSED",
        "count": len(created_txns),
        "transaction_ids": created_txns,
        "high_risk_count": sum(1 for e in evaluations if e['risk_level'] in ['HIGH', 'CRITICAL'])
    }

@router.get("", response_model=Dict[str, Any])
def list_transactions(
    search: Optional[str] = Query(None, description="Search by transaction ID or account"),
    txn_type: Optional[str] = Query(None, description="Filter by transaction type"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Lists transactions with compound querying across MongoDB collections.
    """
    txns_col = get_collection("transactions")
    preds_col = get_collection("predictions")
    
    query: Dict[str, Any] = {}
    if search and isinstance(search, str):
        query["$or"] = [
            {"transaction_id": {"$regex": search, "$options": "i"}},
            {"origin_account": {"$regex": search, "$options": "i"}},
            {"destination_account": {"$regex": search, "$options": "i"}}
        ]
    if txn_type and isinstance(txn_type, str):
        query["transaction_type"] = txn_type.upper()
    if (min_amount is not None and isinstance(min_amount, (int, float))) or (max_amount is not None and isinstance(max_amount, (int, float))):
        query["amount"] = {}
        if min_amount is not None and isinstance(min_amount, (int, float)):
            query["amount"]["$gte"] = min_amount
        if max_amount is not None and isinstance(max_amount, (int, float)):
            query["amount"]["$lte"] = max_amount
            
    limit_val = limit if isinstance(limit, int) else 50
    skip_val = skip if isinstance(skip, int) else 0
            
    total = txns_col.count_documents(query)
    raw_txns = list(txns_col.find(query, {"_id": 0}).sort("created_at", -1).skip(skip_val).limit(limit_val))
    
    # Enrich transactions with risk scores
    results = []
    for t in raw_txns:
        p = preds_col.find_one({"transaction_id": t.get("transaction_id")}, {"_id": 0})
        t_risk = p.get("risk_level", "LOW") if p else "LOW"
        t_score = p.get("final_risk_score", 15.0) if p else 15.0
        
        # Apply risk filter if requested
        if risk_level and t_risk != risk_level.upper():
            continue
            
        t["risk_level"] = t_risk
        t["final_risk_score"] = t_score
        t["prediction"] = p
        results.append(t)
        
    return {
        "total": total,
        "returned": len(results),
        "skip": skip,
        "limit": limit,
        "transactions": results
    }

@router.get("/{transaction_id}", response_model=Dict[str, Any])
def get_transaction_details(transaction_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retrieves full transaction context, feature drivers, customer profile, and prediction results.
    """
    txns_col = get_collection("transactions")
    preds_col = get_collection("predictions")
    alerts_col = get_collection("fraud_alerts")
    cust_col = get_collection("customers")
    
    txn = txns_col.find_one({"transaction_id": transaction_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")
        
    prediction = preds_col.find_one({"transaction_id": transaction_id}, {"_id": 0})
    alert = alerts_col.find_one({"transaction_id": transaction_id}, {"_id": 0})
    customer = cust_col.find_one({"account_id": txn.get("origin_account")}, {"_id": 0})
    
    return {
        "transaction": txn,
        "prediction": prediction,
        "alert": alert,
        "origin_customer_profile": customer
    }
