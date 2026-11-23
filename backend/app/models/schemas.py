"""
SentinelX Pydantic Schemas & Domain Models
Validates transaction payloads, ML prediction representations, alert life-cycles,
audit logs, and investigation decisions.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TransactionBase(BaseModel):
    step: int = Field(default=1, description="Simulation step / hour", ge=0)
    transaction_type: str = Field(..., description="TRANSFER, CASH_OUT, PAYMENT, CASH_IN, DEBIT")
    amount: float = Field(..., gt=0, description="Transaction monetary amount")
    origin_account: str = Field(..., description="Sender account identifier e.g. ACC_1001")
    destination_account: str = Field(..., description="Recipient identifier e.g. ACC_2001")
    old_balance_origin: float = Field(default=0.0, ge=0)
    new_balance_origin: float = Field(default=0.0, ge=0)
    old_balance_destination: float = Field(default=0.0, ge=0)
    new_balance_destination: float = Field(default=0.0, ge=0)
    source: Optional[str] = Field(default="api", description="Source channel: api, web, batch, simulator")

class TransactionCreate(TransactionBase):
    transaction_id: Optional[str] = None
    created_at: Optional[str] = None

class TransactionOut(TransactionBase):
    transaction_id: str
    created_at: str
    is_fraud_flag: Optional[int] = None

class FeatureImpact(BaseModel):
    feature: str
    label: str
    shap_value: float
    feature_value: float
    direction: str
    impact: str
    summary: str

class PredictionOut(BaseModel):
    prediction_id: str
    transaction_id: str
    model_version: str
    fraud_probability: float
    anomaly_score: float
    behavioural_score: float
    final_risk_score: float
    risk_level: str
    recommended_action: str
    prediction_time_ms: float
    explanations: List[FeatureImpact] = []
    created_at: str

class AlertOut(BaseModel):
    alert_id: str
    transaction_id: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    status: str   # OPEN, UNDER_REVIEW, RESOLVED, DISMISSED
    reason: List[str]
    assigned_to: Optional[str] = None
    created_at: str
    transaction_details: Optional[Dict[str, Any]] = None
    prediction_details: Optional[Dict[str, Any]] = None

class AlertUpdateStatus(BaseModel):
    status: str
    analyst_id: Optional[str] = "USR_ANALYST_1"
    remarks: Optional[str] = None

class AlertAssign(BaseModel):
    assigned_to: str
    analyst_id: Optional[str] = "USR_SUPERVISOR"

class InvestigationCreate(BaseModel):
    alert_id: str
    analyst_id: str
    decision: str # CONFIRMED_FRAUD, LEGITIMATE_TRANSACTION, SUSPICIOUS_ESCALATED
    remarks: str

class InvestigationOut(BaseModel):
    investigation_id: str
    alert_id: str
    analyst_id: str
    decision: str
    remarks: str
    reviewed_at: str

class CustomerProfile(BaseModel):
    account_id: str
    account_type: str = "INDIVIDUAL"
    transaction_count: int = 0
    average_transaction_amount: float = 0.0
    last_transaction_time: Optional[str] = None
    risk_history: Dict[str, Any] = {"previous_alerts": 0, "confirmed_fraud_cases": 0}

class ModelRegistryItem(BaseModel):
    model_id: str
    model_name: str
    version: str
    algorithm: str
    precision: float
    recall: float
    pr_auc: float
    roc_auc: Optional[float] = None
    training_date: str
    status: str # ACTIVE, ARCHIVED, STAGING

class AuditLogItem(BaseModel):
    event_id: str
    user_id: str
    action: str
    resource_id: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    timestamp: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_role: str
    username: str
