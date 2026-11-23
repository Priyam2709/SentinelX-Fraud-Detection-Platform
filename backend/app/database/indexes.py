"""
SentinelX MongoDB Indexing Strategy
Builds single-field and compound indexes required for sub-millisecond query latency:
- Unique constraints on primary entity identifiers
- Compound indexes for high-throughput dashboard filtering (e.g. status + severity)
- Chronological indexes for audit logs and prediction trends
"""

import logging
from pymongo import ASCENDING, DESCENDING
from backend.app.database.connection import get_database

logger = logging.getLogger("sentinelx.indexes")

def create_all_indexes():
    """
    Creates indexes across all 7 core collections.
    """
    db = get_database()
    logger.info("Initializing MongoDB indexes across 7 core collections...")
    
    try:
        # 1. transactions
        db.transactions.create_index([("transaction_id", ASCENDING)], unique=True)
        db.transactions.create_index([("origin_account", ASCENDING), ("created_at", DESCENDING)])
        db.transactions.create_index([("destination_account", ASCENDING)])
        db.transactions.create_index([("created_at", DESCENDING)])
        
        # 2. predictions
        db.predictions.create_index([("transaction_id", ASCENDING)])
        db.predictions.create_index([("risk_level", ASCENDING), ("created_at", DESCENDING)])
        db.predictions.create_index([("final_risk_score", DESCENDING)])
        
        # 3. fraud_alerts
        db.fraud_alerts.create_index([("status", ASCENDING), ("severity", ASCENDING)])
        db.fraud_alerts.create_index([("created_at", DESCENDING)])
        db.fraud_alerts.create_index([("alert_id", ASCENDING)], unique=True)
        db.fraud_alerts.create_index([("assigned_to", ASCENDING)])
        
        # 4. customers
        db.customers.create_index([("account_id", ASCENDING)], unique=True)
        
        # 5. investigations
        db.investigations.create_index([("alert_id", ASCENDING)])
        db.investigations.create_index([("analyst_id", ASCENDING)])
        db.investigations.create_index([("reviewed_at", DESCENDING)])
        
        # 6. model_registry
        db.model_registry.create_index([("model_id", ASCENDING)], unique=True)
        db.model_registry.create_index([("status", ASCENDING)])
        
        # 7. audit_logs
        db.audit_logs.create_index([("timestamp", DESCENDING)])
        db.audit_logs.create_index([("resource_id", ASCENDING)])
        
        logger.info("All 7 collection indexes verified and built successfully.")
    except Exception as e:
        logger.warning(f"Note on index creation: {e}")
