"""
SentinelX Machine Learning & Hybrid Risk Engine Test Suite
"""

import unittest
import pandas as pd
import numpy as np

from ml.data.dataset_generator import generate_synthetic_paysim
from ml.feature_engineering.engineer import engineer_features, prepare_train_test_split, FEATURE_COLUMNS
from backend.app.services.risk_engine import BehaviouralRiskEngine, compute_hybrid_risk_score
from backend.app.services.fraud_service import get_fraud_service

class TestSentinelXML(unittest.TestCase):
    def setUp(self):
        self.raw_txn = {
            "step": 120,
            "type": "TRANSFER",
            "amount": 95000.0,
            "oldbalanceOrg": 95000.0,
            "newbalanceOrig": 0.0,
            "nameOrig": "ACC_TEST_ORIG",
            "nameDest": "ACC_TEST_DEST",
            "oldbalanceDest": 0.0,
            "newbalanceDest": 95000.0
        }

    def test_feature_engineering_integrity(self):
        df = pd.DataFrame([self.raw_txn])
        features = engineer_features(df)
        
        # Verify exact column schema
        self.assertEqual(list(features.columns), FEATURE_COLUMNS)
        self.assertFalse(features.isnull().values.any())
        
        # Verify domain balance features
        self.assertEqual(features['balance_drained'].iloc[0], 1)
        self.assertEqual(features['dest_zero_old'].iloc[0], 1)
        self.assertEqual(features['type_TRANSFER'].iloc[0], 1)

    def test_leakage_prevention(self):
        df = generate_synthetic_paysim(n_samples=50, random_state=42)
        X_train, X_test, y_train, y_test = prepare_train_test_split(df, test_size=0.2)
        
        # Ensure isFlaggedFraud is strictly excluded from features
        self.assertNotIn('isFlaggedFraud', X_train.columns)
        self.assertNotIn('isFlaggedFraud', X_test.columns)

    def test_behavioural_risk_engine(self):
        engine = BehaviouralRiskEngine()
        result = engine.evaluate_behavioural_risk(self.raw_txn)
        
        self.assertGreaterEqual(result['behavioural_score'], 40.0)
        self.assertTrue(len(result['triggered_indicators']) >= 2)
        rule_names = [r['rule'] for r in result['triggered_indicators']]
        self.assertIn('COMPLETE_BALANCE_DRAIN', rule_names)

    def test_hybrid_risk_calibration_formula(self):
        # R = 0.65*P + 0.20*A + 0.15*B
        # P = 0.90 (90), A = 0.80 (80), B = 70.0
        # R = 0.65*90 + 0.20*80 + 0.15*70 = 58.5 + 16.0 + 10.5 = 85.0 -> CRITICAL
        res = compute_hybrid_risk_score(0.90, 0.80, 70.0)
        self.assertEqual(res['final_risk_score'], 85.0)
        self.assertEqual(res['risk_level'], 'CRITICAL')
        self.assertEqual(res['recommended_action'], 'URGENT_INVESTIGATION')

    def test_end_to_end_fraud_service(self):
        fs = get_fraud_service()
        eval_res = fs.evaluate_transaction(self.raw_txn, persist=False)
        
        self.assertIn('final_risk_score', eval_res)
        self.assertIn('risk_level', eval_res)
        self.assertIn('explanations', eval_res)
        self.assertGreater(len(eval_res['explanations']), 0)
        self.assertGreater(eval_res['prediction_time_ms'], 0)

if __name__ == '__main__':
    unittest.main()
