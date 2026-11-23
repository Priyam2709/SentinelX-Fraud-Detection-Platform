"""
SentinelX Fraud Service Engine
Coordinates:
1. Feature extraction and validation
2. Layer 1: XGBoost Supervised Classification
3. Layer 2: Isolation Forest Anomaly Detection
4. Layer 3: Behavioural Risk Rule Evaluation
5. SHAP Transaction Explainability
6. MongoDB Persistence across predictions, alerts, and customer profile collections
"""

import os
import time
import uuid
import joblib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from backend.app.config import settings
from backend.app.database.connection import get_collection
from backend.app.services.risk_engine import BehaviouralRiskEngine, compute_hybrid_risk_score
from ml.feature_engineering.engineer import engineer_features, FEATURE_COLUMNS
from ml.explainability.shap_explainer import SentinelXExplainer

logger = logging.getLogger("sentinelx.fraud_service")

class FraudService:
    def __init__(self):
        self.behavioural_engine = BehaviouralRiskEngine()
        self.xgb_model = None
        self.iso_model = None
        self.scaler = None
        self.explainer = None
        self._load_models()

    def _load_models(self):
        models_dir = settings.MODELS_DIR
        try:
            xgb_path = os.path.join(models_dir, 'xgboost_model.joblib')
            iso_path = os.path.join(models_dir, 'isolation_forest.joblib')
            scaler_path = os.path.join(models_dir, 'scaler.joblib')
            
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
                logger.info("Loaded XGBoost model artifact successfully.")
            if os.path.exists(iso_path):
                self.iso_model = joblib.load(iso_path)
                logger.info("Loaded Isolation Forest model artifact.")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                
            if self.xgb_model is not None:
                self.explainer = SentinelXExplainer(self.xgb_model, FEATURE_COLUMNS)
        except Exception as e:
            logger.error(f"Error loading model artifacts: {e}")

    def evaluate_transaction(self, txn_dict: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
        """
        Processes a single transaction through the full 3-layer risk intelligence pipeline.
        """
        start_time = time.perf_counter()
        
        # Format payload into dataframe for feature engineering
        df_raw = pd.DataFrame([{
            'amount': float(txn_dict.get('amount', 0)),
            'oldbalanceOrg': float(txn_dict.get('old_balance_origin', txn_dict.get('oldbalanceOrg', 0))),
            'newbalanceOrig': float(txn_dict.get('new_balance_origin', txn_dict.get('newbalanceOrig', 0))),
            'oldbalanceDest': float(txn_dict.get('old_balance_destination', txn_dict.get('oldbalanceDest', 0))),
            'newbalanceDest': float(txn_dict.get('new_balance_destination', txn_dict.get('newbalanceDest', 0))),
            'nameDest': str(txn_dict.get('destination_account', txn_dict.get('nameDest', ''))),
            'type': str(txn_dict.get('transaction_type', txn_dict.get('type', 'TRANSFER'))).upper(),
            'step': int(txn_dict.get('step', 1))
        }])
        
        # 1. Feature Engineering
        X_features = engineer_features(df_raw)
        
        # 2. Layer 1: Supervised XGBoost Inference
        p_supervised = 0.05
        if self.xgb_model is not None:
            try:
                probs = self.xgb_model.predict_proba(X_features)
                p_supervised = float(probs[0, 1])
            except Exception as e:
                logger.warning(f"XGBoost prediction error: {e}")
                p_supervised = 0.5
                
        # 3. Layer 2: Unsupervised Anomaly Scoring (Isolation Forest)
        anomaly_score = 0.1
        if self.iso_model is not None:
            try:
                # Decision function: lower values mean more anomalous
                decision_val = self.iso_model.decision_function(X_features)[0]
                # Normalize decision function (typically -0.5 to +0.5) to [0, 1] anomaly score
                anomaly_score = float(np.clip(0.5 - decision_val, 0.0, 1.0))
            except Exception as e:
                logger.warning(f"Anomaly scoring error: {e}")
                anomaly_score = 0.2
                
        # 4. Layer 3: Behavioural Risk Engine
        origin_acc = str(txn_dict.get('origin_account', txn_dict.get('nameOrig', 'ACC_DEFAULT')))
        customer_profile = self._get_customer_profile(origin_acc)
        behavioural_result = self.behavioural_engine.evaluate_behavioural_risk(txn_dict, customer_profile)
        b_score = behavioural_result['behavioural_score']
        
        # 5. Hybrid Risk Calibration
        old_orig_val = float(txn_dict.get('old_balance_origin', txn_dict.get('oldbalanceOrg', 0)))
        new_orig_val = float(txn_dict.get('new_balance_origin', txn_dict.get('newbalanceOrig', 0)))
        amt_val = float(txn_dict.get('amount', 0))
        t_type_val = str(txn_dict.get('transaction_type', txn_dict.get('type', 'TRANSFER'))).upper()
        is_drain = (old_orig_val > 0 and new_orig_val == 0.0 and t_type_val in ['TRANSFER', 'CASH_OUT'])
        
        risk_result = compute_hybrid_risk_score(
            p_supervised=p_supervised,
            anomaly_score_normalized=anomaly_score,
            b_score=b_score,
            is_complete_drain=is_drain,
            amount=amt_val
        )
        
        # 6. SHAP Explanations
        explanations = []
        if self.explainer:
            explanations = self.explainer.explain_transaction(X_features)
            
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        prediction_id = f"PRED_{uuid.uuid4().hex[:8].upper()}"
        txn_id = txn_dict.get('transaction_id', f"TXN_{uuid.uuid4().hex[:8].upper()}")
        timestamp = txn_dict.get('created_at', datetime.utcnow().isoformat() + "Z")
        
        result_payload = {
            'prediction_id': prediction_id,
            'transaction_id': txn_id,
            'model_version': settings.ACTIVE_MODEL_VERSION,
            'fraud_probability': round(p_supervised, 4),
            'anomaly_score': round(anomaly_score, 4),
            'behavioural_score': round(b_score, 2),
            'final_risk_score': risk_result['final_risk_score'],
            'risk_level': risk_result['risk_level'],
            'recommended_action': risk_result['recommended_action'],
            'prediction_time_ms': elapsed_ms,
            'explanations': explanations[:6], # top 6 feature drivers
            'triggered_indicators': behavioural_result['triggered_indicators'],
            'created_at': timestamp
        }
        
        if persist:
            self._persist_evaluation(txn_dict, result_payload, explanations)
            
        return result_payload

    def _get_customer_profile(self, account_id: str) -> Optional[Dict[str, Any]]:
        try:
            customers_col = get_collection("customers")
            return customers_col.find_one({"account_id": account_id}, {"_id": 0})
        except Exception:
            return None

    def _persist_evaluation(self, txn_dict: Dict[str, Any], pred: Dict[str, Any], explanations: List[Dict[str, Any]]):
        """Persists transaction inference into MongoDB across collections."""
        try:
            # 1. Save Prediction
            pred_col = get_collection("predictions")
            pred_record = pred.copy()
            pred_col.insert_one(pred_record)
            
            # 2. Update Customer Profile
            cust_col = get_collection("customers")
            orig_acc = txn_dict.get('origin_account', txn_dict.get('nameOrig', 'ACC_DEFAULT'))
            amt = float(txn_dict.get('amount', 0))
            
            cust = cust_col.find_one({"account_id": orig_acc})
            if cust:
                cnt = cust.get('transaction_count', 0) + 1
                curr_avg = cust.get('average_transaction_amount', amt)
                new_avg = round(((curr_avg * (cnt - 1)) + amt) / cnt, 2)
                prev_alerts = cust.get('risk_history', {}).get('previous_alerts', 0)
                if pred['risk_level'] in ['HIGH', 'CRITICAL']:
                    prev_alerts += 1
                    
                cust_col.update_one(
                    {"account_id": orig_acc},
                    {"$set": {
                        "transaction_count": cnt,
                        "average_transaction_amount": new_avg,
                        "last_transaction_time": pred['created_at'],
                        "risk_history.previous_alerts": prev_alerts
                    }}
                )
            else:
                cust_col.insert_one({
                    "account_id": orig_acc,
                    "account_type": "INDIVIDUAL",
                    "transaction_count": 1,
                    "average_transaction_amount": amt,
                    "last_transaction_time": pred['created_at'],
                    "risk_history": {
                        "previous_alerts": 1 if pred['risk_level'] in ['HIGH', 'CRITICAL'] else 0,
                        "confirmed_fraud_cases": 0
                    }
                })
                
            # 3. Create Alert if High or Critical Risk
            if pred['risk_level'] in ['HIGH', 'CRITICAL']:
                alerts_col = get_collection("fraud_alerts")
                alert_id = f"ALT_{uuid.uuid4().hex[:8].upper()}"
                
                # Derive human reasons from top explanations and triggered indicators
                reasons = []
                for ind in pred.get('triggered_indicators', []):
                    reasons.append(ind['description'])
                for exp in explanations[:3]:
                    if exp['direction'] == 'INCREASED_RISK':
                        reasons.append(exp['summary'])
                if not reasons:
                    reasons = ["Elevated model fraud probability and abnormal pattern"]
                    
                alert_doc = {
                    "alert_id": alert_id,
                    "transaction_id": pred['transaction_id'],
                    "severity": pred['risk_level'],
                    "status": "OPEN",
                    "reason": reasons[:4],
                    "assigned_to": None,
                    "created_at": pred['created_at']
                }
                alerts_col.insert_one(alert_doc)
                
                # 4. Audit Log
                audit_col = get_collection("audit_logs")
                audit_col.insert_one({
                    "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
                    "user_id": "SYSTEM_DETECTION_ENGINE",
                    "action": "FRAUD_ALERT_GENERATED",
                    "resource_id": alert_id,
                    "previous_status": None,
                    "new_status": "OPEN",
                    "timestamp": pred['created_at']
                })
                
        except Exception as e:
            logger.error(f"Persistence error: {e}")

_fraud_service = None

def get_fraud_service() -> FraudService:
    global _fraud_service
    if _fraud_service is None:
        _fraud_service = FraudService()
    return _fraud_service
