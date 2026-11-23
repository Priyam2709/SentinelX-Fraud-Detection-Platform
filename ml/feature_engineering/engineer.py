"""
SentinelX Feature Engineering Pipeline
Constructs mathematically sound fraud indicators while strictly preventing label leakage.
Features:
- errorBalanceOrig: arithmetic balance delta in originating account
- errorBalanceDest: arithmetic balance delta in destination account
- balance_drained: flag if originating account was emptied to zero
- dest_zero_old: flag if destination began with zero balance
- amount_to_orig_ratio: ratio of amount transferred to pre-existing balance
- is_merchant_dest: flag if recipient is merchant (starts with 'M')
- hour_of_day, day_of_month: cyclical temporal features from simulation step
- one-hot encoded transaction types (TRANSFER, CASH_OUT, PAYMENT, CASH_IN, DEBIT)
"""

import numpy as np
import pandas as pd
from typing import Tuple, List

FEATURE_COLUMNS = [
    'amount',
    'oldbalanceOrg',
    'newbalanceOrig',
    'oldbalanceDest',
    'newbalanceDest',
    'errorBalanceOrig',
    'errorBalanceDest',
    'balance_drained',
    'dest_zero_old',
    'amount_to_orig_ratio',
    'is_merchant_dest',
    'hour_of_day',
    'type_CASH_IN',
    'type_CASH_OUT',
    'type_DEBIT',
    'type_PAYMENT',
    'type_TRANSFER'
]

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw PaySim transaction records into ML feature vectors.
    """
    data = df.copy()
    
    # 1. Arithmetic Balance Error Check
    # In normal transactions: newbalanceOrig = oldbalanceOrg - amount => error should be 0
    data['errorBalanceOrig'] = data['newbalanceOrig'] + data['amount'] - data['oldbalanceOrg']
    
    # In normal transactions: newbalanceDest = oldbalanceDest + amount => error should be 0
    data['errorBalanceDest'] = data['oldbalanceDest'] + data['amount'] - data['newbalanceDest']
    
    # 2. Account Behavioural Indicators
    data['balance_drained'] = ((data['oldbalanceOrg'] > 0) & (data['newbalanceOrig'] == 0)).astype(int)
    data['dest_zero_old'] = (data['oldbalanceDest'] == 0).astype(int)
    data['amount_to_orig_ratio'] = np.clip(data['amount'] / (data['oldbalanceOrg'] + 1.0), 0, 100.0)
    
    # 3. Recipient Type
    if 'nameDest' in data.columns:
        data['is_merchant_dest'] = data['nameDest'].astype(str).str.startswith('M').astype(int)
    else:
        data['is_merchant_dest'] = 0
        
    # 4. Temporal Features
    if 'step' in data.columns:
        data['hour_of_day'] = (data['step'] % 24).astype(int)
    else:
        data['hour_of_day'] = 12
        
    # 5. Type One-Hot Encoding
    all_types = ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
    for t in all_types:
        col_name = f'type_{t}'
        if 'type' in data.columns:
            data[col_name] = (data['type'] == t).astype(int)
        else:
            data[col_name] = 0
            
    # Guarantee all expected feature columns exist in exact order
    for col in FEATURE_COLUMNS:
        if col not in data.columns:
            data[col] = 0.0
            
    return data[FEATURE_COLUMNS]

def prepare_train_test_split(df: pd.DataFrame, test_size: float = 0.2, chronological: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Chronological or stratified split preventing data leakage.
    Explicitly removes isFlaggedFraud shortcut.
    """
    clean_df = df.copy()
    # Explicit leakage prevention
    if 'isFlaggedFraud' in clean_df.columns:
        clean_df = clean_df.drop(columns=['isFlaggedFraud'])
        
    if chronological and 'step' in clean_df.columns:
        # Sort chronologically by step
        clean_df = clean_df.sort_values('step').reset_index(drop=True)
        split_idx = int(len(clean_df) * (1 - test_size))
        train_raw = clean_df.iloc[:split_idx]
        test_raw = clean_df.iloc[split_idx:]
    else:
        from sklearn.model_selection import train_test_split
        train_raw, test_raw = train_test_split(clean_df, test_size=test_size, stratify=clean_df['isFraud'], random_state=42)
        
    X_train = engineer_features(train_raw)
    y_train = train_raw['isFraud']
    
    X_test = engineer_features(test_raw)
    y_test = test_raw['isFraud']
    
    return X_train, X_test, y_train, y_test
