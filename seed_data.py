"""
SentinelX Initial Data Seeder
Populates MongoDB with rich, realistic demonstration data across all 7 collections
with a balanced representation of LOW, MEDIUM, HIGH, and CRITICAL risk tiers:
1. transactions
2. predictions
3. fraud_alerts
4. customers
5. investigations
6. model_registry
7. audit_logs
"""

import random
from datetime import datetime, timedelta
import uuid

from backend.app.database.connection import get_collection, get_database
from backend.app.services.fraud_service import get_fraud_service

def seed_initial_records(force_reseed: bool = False):
    txns_col = get_collection("transactions")
    # Only seed if database is empty unless force_reseed is requested
    if not force_reseed and txns_col.count_documents({}) > 0:
        return
        
    if force_reseed:
        # Clear collections for fresh realistic reseed
        for col in ["transactions", "predictions", "fraud_alerts", "customers", "investigations", "audit_logs"]:
            get_collection(col).delete_many({})
            
    print("[INFO] Seeding balanced demonstration records (LOW, MEDIUM, HIGH, CRITICAL) into MongoDB...")
    fraud_service = get_fraud_service()
    
    # Pre-defined suspicious mule ring network for the Graph Visualizer
    # Ring: ACC_MULE_1 -> ACC_MULE_2 -> ACC_MULE_3 -> ACC_MULE_1
    mule_ring_pairs = [
        ("ACC_MULE_1", "ACC_MULE_2", 84000.0, "TRANSFER"),
        ("ACC_MULE_2", "ACC_MULE_3", 83500.0, "TRANSFER"),
        ("ACC_MULE_3", "ACC_MULE_1", 82900.0, "TRANSFER"),
        ("ACC_MULE_3", "ACC_CASH_OUT", 82000.0, "CASH_OUT"),
    ]
    
    base_time = datetime.utcnow() - timedelta(hours=36)
    
    # 1. Seed Mule Ring Transactions (CRITICAL)
    for i, (orig, dest, amt, t_type) in enumerate(mule_ring_pairs):
        t_time = (base_time + timedelta(hours=i*2)).isoformat() + "Z"
        txn = {
            "transaction_id": f"TXN_RING_{100 + i}",
            "step": 200 + i,
            "transaction_type": t_type,
            "amount": amt,
            "origin_account": orig,
            "destination_account": dest,
            "old_balance_origin": amt,
            "new_balance_origin": 0.0,
            "old_balance_destination": 0.0,
            "new_balance_destination": amt if t_type == "TRANSFER" else 0.0,
            "created_at": t_time,
            "source": "api"
        }
        txns_col.insert_one(txn.copy())
        fraud_service.evaluate_transaction(txn, persist=True)
        
    # 2. Seed Structured Transactions Across all 4 Risk Tiers
    # Tier specs:
    tiers_plan = [
        # (Tier, Type, Amount, OldOrig, NewOrig, OldDest, NewDest, OrigAcc, DestAcc)
        # CRITICAL (Score 80-100): Account takeovers, full drainage
        ('CRITICAL', 'TRANSFER', 320000.0, 320000.0, 0.0, 0.0, 320000.0, 'ACC_2001', 'ACC_3001'),
        ('CRITICAL', 'CASH_OUT', 185000.0, 185000.0, 0.0, 0.0, 0.0, 'ACC_2002', 'ACC_3002'),
        
        # HIGH (Score 60-79): Significant drain leaving small balance, or unfunded destination
        ('HIGH', 'TRANSFER', 85000.0, 95000.0, 10000.0, 0.0, 85000.0, 'ACC_2101', 'ACC_3101'),
        ('HIGH', 'CASH_OUT', 72000.0, 78000.0, 6000.0, 0.0, 0.0, 'ACC_2102', 'ACC_3102'),
        ('HIGH', 'TRANSFER', 95000.0, 110000.0, 15000.0, 0.0, 95000.0, 'ACC_2103', 'ACC_3103'),
        
        # MEDIUM (Score 30-59): Unusually large purchase/transfer for customer, but healthy balance & known recipient
        ('MEDIUM', 'TRANSFER', 48000.0, 160000.0, 112000.0, 25000.0, 73000.0, 'ACC_1501', 'ACC_1601'),
        ('MEDIUM', 'CASH_OUT', 38000.0, 120000.0, 82000.0, 15000.0, 53000.0, 'ACC_1502', 'ACC_1602'),
        ('MEDIUM', 'TRANSFER', 52000.0, 210000.0, 158000.0, 42000.0, 94000.0, 'ACC_1503', 'ACC_1603'),
        ('MEDIUM', 'PAYMENT', 34000.0, 90000.0, 56000.0, 0.0, 0.0, 'ACC_1504', 'M_99812'),
        ('MEDIUM', 'TRANSFER', 42000.0, 140000.0, 98000.0, 18000.0, 60000.0, 'ACC_1505', 'ACC_1605'),
        
        # LOW (Score 0-29): Everyday consumer transactions
        ('LOW', 'PAYMENT', 1250.0, 35000.0, 33750.0, 0.0, 0.0, 'ACC_1001', 'M_10023'),
        ('LOW', 'PAYMENT', 3400.0, 42000.0, 38600.0, 0.0, 0.0, 'ACC_1002', 'M_10045'),
        ('LOW', 'PAYMENT', 850.0, 18000.0, 17150.0, 0.0, 0.0, 'ACC_1003', 'M_10089'),
        ('LOW', 'CASH_IN', 15000.0, 12000.0, 27000.0, 50000.0, 65000.0, 'ACC_1004', 'ACC_1005'),
        ('LOW', 'TRANSFER', 6500.0, 85000.0, 78500.0, 32000.0, 38500.0, 'ACC_1006', 'ACC_1007'),
        ('LOW', 'DEBIT', 2100.0, 25000.0, 22900.0, 12000.0, 14100.0, 'ACC_1008', 'ACC_1009'),
        ('LOW', 'PAYMENT', 4900.0, 56000.0, 51100.0, 0.0, 0.0, 'ACC_1010', 'M_10067'),
        ('LOW', 'TRANSFER', 8200.0, 64000.0, 55800.0, 21000.0, 29200.0, 'ACC_1011', 'ACC_1012'),
        ('LOW', 'PAYMENT', 1600.0, 31000.0, 29400.0, 0.0, 0.0, 'ACC_1013', 'M_10078'),
    ]
    
    for idx, (tier, t_type, amt, old_o, new_o, old_d, new_d, orig, dest) in enumerate(tiers_plan):
        t_time = (base_time + timedelta(minutes=idx * 75)).isoformat() + "Z"
        txn = {
            "transaction_id": f"TXN_{30100 + idx}",
            "step": 150 + idx,
            "transaction_type": t_type,
            "amount": amt,
            "origin_account": orig,
            "destination_account": dest,
            "old_balance_origin": old_o,
            "new_balance_origin": new_o,
            "old_balance_destination": old_d,
            "new_balance_destination": new_d,
            "created_at": t_time,
            "source": "api"
        }
        txns_col.insert_one(txn.copy())
        fraud_service.evaluate_transaction(txn, persist=True)
        
    # 3. Add Pre-built Investigations to demonstrate the completed workflow
    alerts_col = get_collection("fraud_alerts")
    inv_col = get_collection("investigations")
    
    sample_alerts = list(alerts_col.find({}).limit(3))
    decisions = [
        ("CONFIRMED_FRAUD", "Account takeover confirmed. Customer contacted via out-of-band SMS. Funds recalled."),
        ("LEGITIMATE_TRANSACTION", "Customer verified large commercial equipment purchase. Documented invoice provided."),
        ("CONFIRMED_FRAUD", "Smurfing mule behavior. Linked to known fraudulent syndicate.")
    ]
    for idx, alert in enumerate(sample_alerts):
        if idx < len(decisions):
            dec, rem = decisions[idx]
            inv_col.insert_one({
                "investigation_id": f"INV_{uuid.uuid4().hex[:8].upper()}",
                "alert_id": alert["alert_id"],
                "analyst_id": "USR_101",
                "decision": dec,
                "remarks": rem,
                "reviewed_at": (datetime.utcnow() - timedelta(hours=idx*4)).isoformat() + "Z"
            })
            alerts_col.update_one(
                {"alert_id": alert["alert_id"]},
                {"$set": {"status": "RESOLVED", "resolved_decision": dec}}
            )
            
    # Check distribution
    preds_col = get_collection("predictions")
    dist = {}
    for p in preds_col.find({}):
        lvl = p.get("risk_level", "UNKNOWN")
        dist[lvl] = dist.get(lvl, 0) + 1
        
    print(f"[OK] Seed complete: {txns_col.count_documents({})} transactions, {alerts_col.count_documents({})} alerts.")
    print(f"[OK] Risk tier distribution across database: {dist}")

if __name__ == "__main__":
    seed_initial_records(force_reseed=True)
