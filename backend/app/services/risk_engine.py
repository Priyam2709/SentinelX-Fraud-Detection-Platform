"""
SentinelX Behavioural Risk Engine & Hybrid Multi-Layer Risk Scorer
Combines:
- Layer 1: Supervised XGBoost Probability (P)
- Layer 2: Unsupervised Isolation Forest Anomaly Score (A)
- Layer 3: Dynamic Rule-Based Behavioural Risk Indicators (B)

Formula:
  Final Risk Score R = (0.65 * P) + (0.20 * A) + (0.15 * B)
Normalized to 0..100 with calibrated operational risk bands:
  0 - 29:  LOW (Normal monitoring)
  30 - 59: MEDIUM (Enhanced monitoring / 2FA step-up)
  60 - 79: HIGH (Analyst review required)
  80 - 100: CRITICAL (Urgent investigation & payout hold)
"""

from typing import Dict, Any, List

class BehaviouralRiskEngine:
    def __init__(self):
        # Configurable indicator weights summing to 100
        self.weights = {
            'unusual_amount': 25.0,
            'high_velocity': 25.0,
            'unusual_balance_drain': 25.0,
            'suspicious_history': 25.0,
            'new_destination_unfunded': 20.0
        }

    def evaluate_behavioural_risk(self, txn: Dict[str, Any], customer_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluates behavioural risk indicators against the transaction and optional customer history.
        Returns a normalized score (0..100) and list of triggered indicators.
        """
        score = 0.0
        triggered_indicators = []
        amount = float(txn.get('amount', 0))
        old_orig = float(txn.get('old_balance_origin', txn.get('oldbalanceOrg', 0)))
        new_orig = float(txn.get('new_balance_origin', txn.get('newbalanceOrig', 0)))
        old_dest = float(txn.get('old_balance_destination', txn.get('oldbalanceDest', 0)))
        txn_type = str(txn.get('type', txn.get('transaction_type', 'PAYMENT'))).upper()
        
        # 1. Unusual transaction amount relative to baseline
        avg_amt = 3500.0
        if customer_profile and customer_profile.get('average_transaction_amount'):
            avg_amt = float(customer_profile['average_transaction_amount'])
            
        if amount > (avg_amt * 8) or amount > 45000:
            score += self.weights['unusual_amount']
            triggered_indicators.append({
                'rule': 'UNUSUAL_TRANSACTION_AMOUNT',
                'description': f'Amount ₹{amount:,.2f} sharply exceeds normal customer baseline (₹{avg_amt:,.2f})',
                'weight': self.weights['unusual_amount']
            })
            
        # 2. High Transaction Velocity / rapid succession
        txn_count = 1
        if customer_profile and customer_profile.get('recent_velocity_count'):
            txn_count = int(customer_profile['recent_velocity_count'])
        if txn_count >= 4 or txn.get('velocity_burst', False):
            score += self.weights['high_velocity']
            triggered_indicators.append({
                'rule': 'HIGH_TRANSACTION_VELOCITY',
                'description': f'High velocity burst ({txn_count} transactions in rapid succession)',
                'weight': self.weights['high_velocity']
            })
            
        # 3. Unusual balance drain (entire balance emptied to 0)
        if old_orig > 5000 and new_orig == 0.0 and txn_type in ['TRANSFER', 'CASH_OUT']:
            score += self.weights['unusual_balance_drain']
            triggered_indicators.append({
                'rule': 'COMPLETE_BALANCE_DRAIN',
                'description': f'Originating balance (₹{old_orig:,.2f}) was entirely emptied in a single transaction',
                'weight': self.weights['unusual_balance_drain']
            })
        elif old_orig > 20000 and (amount / (old_orig + 1.0)) >= 0.85 and txn_type in ['TRANSFER', 'CASH_OUT']:
            # Near-total drain (85%+ of funds removed)
            score += 15.0
            triggered_indicators.append({
                'rule': 'NEAR_TOTAL_BALANCE_DRAIN',
                'description': f'Near-total account drain ({(amount/old_orig)*100:.1f}% of funds transferred)',
                'weight': 15.0
            })
            
        # 4. Previously suspicious account history
        prev_alerts = 0
        if customer_profile and customer_profile.get('risk_history'):
            prev_alerts = customer_profile['risk_history'].get('previous_alerts', 0)
        if prev_alerts > 0:
            weight_val = min(self.weights['suspicious_history'], prev_alerts * 12.0)
            score += weight_val
            triggered_indicators.append({
                'rule': 'SUSPICIOUS_ACCOUNT_HISTORY',
                'description': f'Account has {prev_alerts} previous fraud alerts on record',
                'weight': weight_val
            })
            
        # 5. New or Unfunded Destination
        if old_dest == 0.0 and txn_type in ['TRANSFER', 'CASH_OUT'] and amount > 15000:
            score += self.weights['new_destination_unfunded']
            triggered_indicators.append({
                'rule': 'NEW_UNFUNDED_DESTINATION',
                'description': 'Recipient account was previously empty or newly created',
                'weight': self.weights['new_destination_unfunded']
            })
            
        normalized_score = min(100.0, max(0.0, score))
        return {
            'behavioural_score': round(normalized_score, 2),
            'triggered_indicators': triggered_indicators
        }

def compute_hybrid_risk_score(
    p_supervised: float,
    anomaly_score_normalized: float,
    b_score: float,
    is_complete_drain: bool = False,
    amount: float = 0.0
) -> Dict[str, Any]:
    """
    Calibrated hybrid multi-layer risk scoring:
      R = 0.65 * P + 0.20 * A + 0.15 * B
    With balanced domain calibration across the 4 operational tiers:
      LOW:      0 - 29 (Routine normal transactions)
      MEDIUM:  30 - 59 (Unusual amount, moderate anomaly, 2FA step-up)
      HIGH:    60 - 79 (High risk indicators, unfunded recipient, partial drain)
      CRITICAL:80 - 100 (Total account drain to 0, massive unauthorized takeover >= 200k)
    """
    p_val = max(0.0, min(100.0, p_supervised * 100.0))
    a_val = max(0.0, min(100.0, anomaly_score_normalized * 100.0))
    b_val = max(0.0, min(100.0, b_score))
    
    # Base weighted formula
    raw_score = (0.65 * p_val) + (0.20 * a_val) + (0.15 * b_val)
    
    # Operational Tier Calibration:
    # 1. Total balance drain to 0 OR massive takeover (>= 200k) OR overwhelming raw score (>= 85.0) -> CRITICAL (80-100)
    if is_complete_drain or amount >= 200000.0 or raw_score >= 85.0:
        final_score = min(100.0, max(80.0, raw_score))
    # 2. Significant partial drain, unfunded recipient, or elevated model probability -> HIGH (60-79)
    elif raw_score >= 60.0 or p_val >= 45.0 or b_val >= 35.0:
        final_score = min(79.0, max(60.0, (0.50 * p_val) + (0.30 * a_val) + (0.20 * b_val)))
    # 3. Moderate single-indicator anomaly (unusual amount or new recipient) -> MEDIUM (30-59)
    elif raw_score >= 30.0 or b_val >= 20.0 or a_val >= 40.0 or p_val >= 18.0:
        final_score = min(59.0, max(30.0, (0.40 * p_val) + (0.35 * a_val) + (0.25 * b_val)))
    # 4. Routine low-risk consumer transactions -> LOW (0-29)
    else:
        final_score = min(29.0, raw_score)
        
    final_score = round(max(0.0, min(100.0, final_score)), 1)
    
    # Risk Bands
    if final_score < 30.0:
        risk_level = 'LOW'
        recommended_action = 'NORMAL_MONITORING'
    elif final_score < 60.0:
        risk_level = 'MEDIUM'
        recommended_action = 'ENHANCED_MONITORING'
    elif final_score < 80.0:
        risk_level = 'HIGH'
        recommended_action = 'ANALYST_REVIEW'
    else:
        risk_level = 'CRITICAL'
        recommended_action = 'URGENT_INVESTIGATION'
        
    return {
        'final_risk_score': final_score,
        'risk_level': risk_level,
        'recommended_action': recommended_action,
        'components': {
            'supervised_probability': round(p_supervised, 4),
            'supervised_score': round(p_val, 1),
            'anomaly_score': round(a_val, 1),
            'behavioural_score': round(b_val, 1)
        }
    }
