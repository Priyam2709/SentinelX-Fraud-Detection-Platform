"""
SentinelX - Data Generation and PaySim Feature Schema
Generates realistic PaySim-compliant financial transactions with a natural, continuous
spectrum of risk behaviors across all 4 tiers (LOW, MEDIUM, HIGH, CRITICAL):
- Routine daily consumer payments and salary deposits (LOW: 0-29)
- Large business purchases, first-time transfers, and single-indicator anomalies (MEDIUM: 30-59)
- Stealth smurfing, partial balance drains to unfunded accounts, and velocity bursts (HIGH: 60-79)
- Total account takeovers, complete account drainage, and massive unauthorized cash-outs (CRITICAL: 80-100)
"""

import numpy as np
import pandas as pd
import random

TYPES = ['TRANSFER', 'CASH_OUT', 'PAYMENT', 'CASH_IN', 'DEBIT']
TYPE_PROBS = [0.18, 0.32, 0.30, 0.18, 0.02]

def generate_synthetic_paysim(n_samples: int = 15000, fraud_ratio: float = 0.08, random_state: int = 42) -> pd.DataFrame:
    np.random.seed(random_state)
    random.seed(random_state)
    
    n_fraud = int(n_samples * fraud_ratio)
    n_legit = n_samples - n_fraud
    
    records = []
    
    # 1. Generate Legitimate Transactions across diverse profiles (Low to Medium Risk)
    for i in range(n_legit):
        step = random.randint(1, 720)
        profile_rand = random.random()
        
        if profile_rand < 0.20:
            # Moderate/Elevated legitimate transfer (e.g. rent, business equipment, tuition)
            # Produces legitimate MEDIUM risk edge cases
            txn_type = random.choice(['TRANSFER', 'PAYMENT'])
            amount = round(float(np.random.uniform(25000, 75000)), 2)
            old_orig = round(amount + np.random.uniform(20000, 120000), 2)
            new_orig = max(0.0, round(old_orig - amount, 2))
            name_dest = f"C{random.randint(1000000, 9999999)}"
            old_dest = round(float(np.random.uniform(5000, 80000)), 2)
            new_dest = round(old_dest + amount, 2)
        elif profile_rand < 0.25:
            # Legitimate account closure / paying off loan in full (draining to 0)
            txn_type = random.choice(['TRANSFER', 'PAYMENT'])
            amount = round(float(np.random.uniform(15000, 45000)), 2)
            old_orig = amount
            new_orig = 0.0
            name_dest = f"M{random.randint(1000000, 9999999)}"
            old_dest = 0.0
            new_dest = 0.0
        elif profile_rand < 0.55:
            # Routine merchant payment
            txn_type = 'PAYMENT'
            amount = round(float(np.random.exponential(scale=3500) + 150), 2)
            name_dest = f"M{random.randint(1000000, 9999999)}"
            old_dest = 0.0
            new_dest = 0.0
            old_orig = round(float(amount + np.random.exponential(scale=15000)), 2)
            new_orig = max(0.0, round(old_orig - amount, 2))
        elif profile_rand < 0.75:
            # Routine salary or cash-in deposit
            txn_type = 'CASH_IN'
            amount = round(float(np.random.exponential(scale=18000) + 500), 2)
            name_dest = f"C{random.randint(1000000, 9999999)}"
            old_dest = round(float(np.random.exponential(scale=25000)), 2)
            new_dest = round(old_dest + amount, 2)
            old_orig = round(float(amount + np.random.exponential(scale=20000)), 2)
            new_orig = max(0.0, round(old_orig - amount, 2))
        elif profile_rand < 0.85:
            # Card POS debit
            txn_type = 'DEBIT'
            amount = round(float(np.random.exponential(scale=4500) + 200), 2)
            name_dest = f"C{random.randint(1000000, 9999999)}"
            old_dest = round(float(np.random.exponential(scale=18000)), 2)
            new_dest = round(old_dest + amount, 2)
            old_orig = round(float(amount + np.random.exponential(scale=10000)), 2)
            new_orig = max(0.0, round(old_orig - amount, 2))
        else:
            # Standard peer-to-peer transfer
            txn_type = random.choice(['TRANSFER', 'CASH_OUT'])
            amount = round(float(np.random.exponential(scale=12000) + 500), 2)
            name_dest = f"C{random.randint(1000000, 9999999)}"
            old_dest = round(float(np.random.exponential(scale=22000)), 2)
            new_dest = round(old_dest + amount, 2)
            old_orig = round(float(amount + np.random.exponential(scale=15000)), 2)
            new_orig = max(0.0, round(old_orig - amount, 2))
            
        name_orig = f"ACC_{random.randint(1000, 1999)}"
        txn_id = f"TXN_{10000 + i}"
        
        records.append({
            'transaction_id': txn_id,
            'step': step,
            'type': txn_type,
            'amount': amount,
            'nameOrig': name_orig,
            'oldbalanceOrg': old_orig,
            'newbalanceOrig': new_orig,
            'nameDest': name_dest,
            'oldbalanceDest': old_dest,
            'newbalanceDest': new_dest,
            'isFraud': 0,
            'isFlaggedFraud': 0
        })
        
    # 2. Generate Fraudulent Transactions across diverse attack strategies (Medium to Critical Risk)
    for j in range(n_fraud):
        step = random.randint(1, 720)
        txn_type = random.choice(['TRANSFER', 'CASH_OUT'])
        attack_type = random.random()
        
        if attack_type < 0.40:
            # A. Full Drain Takeover (CRITICAL: 80-100)
            amount = round(float(np.random.uniform(90000, 750000)), 2)
            old_orig = amount
            new_orig = 0.0
            old_dest = 0.0 if random.random() < 0.70 else round(float(np.random.exponential(scale=5000)), 2)
            new_dest = 0.0 if random.random() < 0.35 else round(old_dest + amount, 2)
        elif attack_type < 0.75:
            # B. Partial Drain to Unfunded Recipient (HIGH: 60-79)
            # High amount, leaves small residual balance (e.g. ₹5k - ₹20k) to evade strict drain rules
            amount = round(float(np.random.uniform(55000, 140000)), 2)
            old_orig = round(amount + np.random.uniform(4000, 25000), 2)
            new_orig = round(old_orig - amount, 2)
            old_dest = 0.0  # Unfunded recipient account
            new_dest = amount
        else:
            # C. Stealth Smurfing / Structuring (MEDIUM/HIGH: 45-65)
            # Transfers just below alert triggers, account has substantial balance
            amount = round(float(np.random.uniform(28000, 52000)), 2)
            old_orig = round(amount + np.random.uniform(40000, 150000), 2)
            new_orig = round(old_orig - amount, 2)
            old_dest = 0.0 if random.random() < 0.60 else round(float(np.random.exponential(scale=4000)), 2)
            new_dest = round(old_dest + amount, 2)
            
        name_orig = f"ACC_{random.randint(2000, 2999)}"
        name_dest = f"ACC_{random.randint(3000, 3999)}"
        txn_id = f"TXN_{200000 + j}"
        
        records.append({
            'transaction_id': txn_id,
            'step': step,
            'type': txn_type,
            'amount': amount,
            'nameOrig': name_orig,
            'oldbalanceOrg': old_orig,
            'newbalanceOrig': new_orig,
            'nameDest': name_dest,
            'oldbalanceDest': old_dest,
            'newbalanceDest': new_dest,
            'isFraud': 1,
            'isFlaggedFraud': 1 if amount > 200000 else 0
        })
        
    df = pd.DataFrame(records)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df
