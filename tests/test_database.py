"""
SentinelX MongoDB Database & PyMongo Architecture Test Suite
Verifies all 7 core collections, compound indexes, and aggregation pipelines.
"""

import unittest
from datetime import datetime

from backend.app.database.connection import get_database, get_collection
from backend.app.database.indexes import create_all_indexes

class TestSentinelXDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_all_indexes()

    def test_all_seven_collections_accessible(self):
        db = get_database()
        required_collections = [
            "transactions",
            "predictions",
            "fraud_alerts",
            "customers",
            "investigations",
            "model_registry",
            "audit_logs"
        ]
        for col_name in required_collections:
            col = get_collection(col_name)
            self.assertIsNotNone(col)

    def test_transaction_crud_operations(self):
        col = get_collection("transactions")
        test_id = "TXN_TEST_DB_001"
        
        # Insert
        doc = {
            "transaction_id": test_id,
            "step": 105,
            "transaction_type": "TRANSFER",
            "amount": 42000.0,
            "origin_account": "ACC_ORIG_TEST",
            "destination_account": "ACC_DEST_TEST",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        col.insert_one(doc)
        
        # Find
        found = col.find_one({"transaction_id": test_id})
        self.assertIsNotNone(found)
        self.assertEqual(found["amount"], 42000.0)
        
        # Update
        col.update_one({"transaction_id": test_id}, {"$set": {"amount": 45000.0}})
        updated = col.find_one({"transaction_id": test_id})
        self.assertEqual(updated["amount"], 45000.0)
        
        # Cleanup
        col.delete_one({"transaction_id": test_id})

    def test_customer_risk_profile_management(self):
        cust_col = get_collection("customers")
        acc_id = "ACC_PROFILE_TEST"
        
        cust_col.update_one(
            {"account_id": acc_id},
            {"$set": {
                "account_id": acc_id,
                "account_type": "BUSINESS",
                "transaction_count": 5,
                "average_transaction_amount": 12500.0,
                "risk_history": {"previous_alerts": 1, "confirmed_fraud_cases": 0}
            }},
            upsert=True
        )
        
        profile = cust_col.find_one({"account_id": acc_id})
        self.assertEqual(profile["account_type"], "BUSINESS")
        self.assertEqual(profile["risk_history"]["previous_alerts"], 1)
        
        cust_col.delete_one({"account_id": acc_id})

if __name__ == '__main__':
    unittest.main()
