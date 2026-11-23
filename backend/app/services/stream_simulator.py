"""
SentinelX Real-Time Transaction Stream Simulator
Generates continuous or on-demand realistic transactions across all 4 risk tiers:
- LOW (0-29): Routine daily purchases, grocery payments, salary deposits
- MEDIUM (30-59): Large purchase anomalies, first-time recipient, moderate velocity
- HIGH (60-79): Significant balance drains, unfunded recipient transfers, velocity bursts
- CRITICAL (80-100): Total account takeovers, immediate multi-lakh cash-outs
"""

import random
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, Any, List

from backend.app.database.connection import get_collection
from backend.app.services.fraud_service import get_fraud_service

class StreamSimulator:
    def __init__(self):
        self.is_running = False
        self._thread = None
        self.fraud_service = None
        self.interval_seconds = 3.0
        self.total_generated = 0

    def generate_single_transaction(self, force_fraud: bool = False) -> Dict[str, Any]:
        """Creates a single realistic transaction spanning LOW, MEDIUM, HIGH, or CRITICAL tiers."""
        if self.fraud_service is None:
            self.fraud_service = get_fraud_service()
            
        txn_id = f"TXN_{random.randint(100000, 999999)}"
        step = random.randint(100, 720)
        
        # Determine risk profile for realistic distribution
        rand = random.random()
        if force_fraud:
            profile = 'CRITICAL'
        elif rand < 0.10:
            profile = 'CRITICAL'
        elif rand < 0.25:
            profile = 'HIGH'
        elif rand < 0.45:
            profile = 'MEDIUM'
        else:
            profile = 'LOW'

        if profile == 'CRITICAL':
            # Complete balance drain + massive transfer/cash-out
            txn_type = random.choice(['TRANSFER', 'CASH_OUT'])
            amount = round(float(random.choice([95000, 180000, 320000, 650000]) + random.uniform(100, 999)), 2)
            old_orig = amount
            new_orig = 0.0 # Fully wiped out
            old_dest = 0.0 if random.random() < 0.75 else round(random.uniform(500, 5000), 2)
            new_dest = 0.0 if random.random() < 0.40 else round(old_dest + amount, 2)
            orig_acc = f"ACC_{random.randint(2000, 2099)}"
            dest_acc = f"ACC_{random.randint(3000, 3099)}"

        elif profile == 'HIGH':
            # High amount + partial balance drain or unfunded destination
            txn_type = random.choice(['TRANSFER', 'CASH_OUT'])
            amount = round(float(random.uniform(55000, 120000)), 2)
            old_orig = round(amount + random.uniform(2000, 15000), 2) # leaves small remainder
            new_orig = round(old_orig - amount, 2)
            old_dest = 0.0 # Unfunded new recipient
            new_dest = amount
            orig_acc = f"ACC_{random.randint(2100, 2199)}"
            dest_acc = f"ACC_{random.randint(3100, 3199)}"

        elif profile == 'MEDIUM':
            # Elevated amount (e.g. ₹35k - ₹65k) or unusual for customer, but healthy balance
            txn_type = random.choice(['TRANSFER', 'PAYMENT', 'CASH_OUT'])
            amount = round(float(random.uniform(28000, 62000)), 2)
            old_orig = round(amount + random.uniform(40000, 150000), 2) # strong remaining balance
            new_orig = round(old_orig - amount, 2)
            old_dest = round(random.uniform(5000, 50000), 2)
            new_dest = round(old_dest + amount, 2)
            orig_acc = f"ACC_{random.randint(1500, 1599)}"
            dest_acc = f"ACC_{random.randint(1600, 1699)}"

        else: # LOW
            # Standard routine payment, debit, or salary cash-in
            txn_type = random.choice(['PAYMENT', 'CASH_IN', 'DEBIT', 'TRANSFER'])
            if txn_type == 'PAYMENT':
                amount = round(random.uniform(150, 4500), 2)
                dest_acc = f"M_{random.randint(10000, 99999)}"
                old_dest = 0.0
                new_dest = 0.0
            else:
                amount = round(random.uniform(800, 18000), 2)
                dest_acc = f"ACC_{random.randint(1000, 1099)}"
                old_dest = round(random.uniform(8000, 60000), 2)
                new_dest = round(old_dest + amount, 2)
                
            old_orig = round(amount + random.uniform(10000, 80000), 2)
            new_orig = max(0.0, round(old_orig - amount, 2))
            orig_acc = f"ACC_{random.randint(1000, 1099)}"

        txn_record = {
            "transaction_id": txn_id,
            "step": step,
            "transaction_type": txn_type,
            "amount": amount,
            "origin_account": orig_acc,
            "destination_account": dest_acc,
            "old_balance_origin": old_orig,
            "new_balance_origin": new_orig,
            "old_balance_destination": old_dest,
            "new_balance_destination": new_dest,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "source": "simulator"
        }
        
        # Save transaction into MongoDB
        txns_col = get_collection("transactions")
        txns_col.insert_one(txn_record.copy())
        
        # Process through Fraud Service
        eval_result = self.fraud_service.evaluate_transaction(txn_record, persist=True)
        self.total_generated += 1
        
        return {
            "transaction": txn_record,
            "evaluation": eval_result
        }

    def start_background_stream(self, interval: float = 3.0):
        if self.is_running:
            return
        self.interval_seconds = interval
        self.is_running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def stop_background_stream(self):
        self.is_running = False

    def _stream_loop(self):
        while self.is_running:
            try:
                self.generate_single_transaction()
            except Exception:
                pass
            time.sleep(self.interval_seconds)

simulator = StreamSimulator()
