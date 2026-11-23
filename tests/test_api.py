"""
SentinelX Comprehensive API & Route Handler Test Suite
Validates transaction submission, risk scoring, alert lifecycle,
investigations, NetworkX graph intelligence, and model metrics.
"""

import unittest
from backend.app.models.schemas import TransactionCreate, AlertUpdateStatus, InvestigationCreate
from backend.app.routes.transactions import submit_transaction, get_transaction_details, list_transactions
from backend.app.routes.predictions import predict_transaction_risk, get_risk_summary
from backend.app.routes.alerts import list_alerts, update_alert_status
from backend.app.routes.investigations import create_investigation, list_investigations
from backend.app.routes.graph import get_transaction_network
from backend.app.routes.models import get_model_evaluation_metrics, list_models
from backend.app.routes.simulator import trigger_simulated_transaction
from backend.app.main import health_check

class TestSentinelXAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.mock_user = {
            "user_id": "USR_101",
            "username": "analyst",
            "role": "ANALYST"
        }
        # Ensure at least 1 high-risk transaction exists
        try:
            submit_transaction(TransactionCreate(
                transaction_id="TXN_TEST_SETUP_001",
                step=100,
                transaction_type="TRANSFER",
                amount=92000.0,
                origin_account="ACC_SETUP_SENDER",
                destination_account="ACC_SETUP_RECEIVER",
                old_balance_origin=92000.0,
                new_balance_origin=0.0,
                old_balance_destination=0.0,
                new_balance_destination=92000.0
            ), current_user=self.mock_user)
        except Exception:
            pass

    def test_health_check_endpoint(self):
        res = health_check()
        self.assertEqual(res["status"], "HEALTHY")
        self.assertTrue(res["models_loaded"])

    def test_transaction_submission_and_detection(self):
        payload = TransactionCreate(
            transaction_id="TXN_TEST_UNIT_999",
            step=125,
            transaction_type="TRANSFER",
            amount=88000.0,
            origin_account="ACC_UNIT_SENDER",
            destination_account="ACC_UNIT_RECEIVER",
            old_balance_origin=88000.0,
            new_balance_origin=0.0,
            old_balance_destination=0.0,
            new_balance_destination=88000.0
        )
        res = submit_transaction(payload, current_user=self.mock_user)
        self.assertEqual(res["status"], "PROCESSED")
        self.assertEqual(res["transaction_id"], "TXN_TEST_UNIT_999")
        self.assertIn("risk_evaluation", res)
        self.assertIn(res["risk_evaluation"]["risk_level"], ["HIGH", "CRITICAL"])
        self.assertTrue(len(res["risk_evaluation"]["explanations"]) > 0)

    def test_get_transaction_details(self):
        res = get_transaction_details("TXN_TEST_SETUP_001", current_user=self.mock_user)
        self.assertIn("transaction", res)
        self.assertIn("prediction", res)
        self.assertEqual(res["transaction"]["amount"], 92000.0)

    def test_risk_summary_aggregation(self):
        res = get_risk_summary(current_user=self.mock_user)
        self.assertIn("kpis", res)
        self.assertIn("risk_distribution", res)
        self.assertGreaterEqual(res["kpis"]["total_transactions"], 1)

    def test_alert_lifecycle_and_investigation(self):
        alerts_res = list_alerts(limit=10, current_user=self.mock_user)
        self.assertIn("alerts", alerts_res)
        self.assertGreater(len(alerts_res["alerts"]), 0)
        
        target_alert = alerts_res["alerts"][0]
        alert_id = target_alert["alert_id"]
        
        up_res = update_alert_status(
            alert_id=alert_id,
            payload=AlertUpdateStatus(status="UNDER_REVIEW", remarks="Initiating analyst triage"),
            current_user=self.mock_user
        )
        self.assertEqual(up_res["status"], "UPDATED")
        self.assertEqual(up_res["new_status"], "UNDER_REVIEW")
        
        inv_payload = InvestigationCreate(
            alert_id=alert_id,
            analyst_id="USR_101",
            decision="CONFIRMED_FRAUD",
            remarks="Verified unauthorized drain from originating device."
        )
        inv_res = create_investigation(inv_payload, current_user=self.mock_user)
        self.assertEqual(inv_res["status"], "RECORDED")
        self.assertIn("investigation_id", inv_res)

    def test_network_graph_intelligence(self):
        res = get_transaction_network(limit=50, current_user=self.mock_user)
        self.assertIn("summary", res)
        self.assertIn("nodes", res)
        self.assertIn("edges", res)
        self.assertGreater(len(res["nodes"]), 0)

    def test_model_observability_and_drift(self):
        res = get_model_evaluation_metrics(current_user=self.mock_user)
        self.assertIn("benchmarks", res)
        self.assertIn("drift_metrics", res)
        self.assertIn("XGBoost (Production)", res["benchmarks"])
        
        models_list = list_models(current_user=self.mock_user)
        self.assertIn("models", models_list)

    def test_simulator_trigger(self):
        sim_res = trigger_simulated_transaction(force_fraud=True, count=1, current_user=self.mock_user)
        self.assertEqual(sim_res["status"], "SUCCESS")
        self.assertEqual(len(sim_res["results"]), 1)

if __name__ == '__main__':
    unittest.main()
