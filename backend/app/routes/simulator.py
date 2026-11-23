"""
SentinelX Real-time Simulation Control APIs
Allows interactive triggering of live transactions, edge case fraud injections,
and continuous streaming.
"""

from fastapi import APIRouter, Query, Depends
from typing import Dict, Any

from backend.app.services.stream_simulator import simulator
from backend.app.security.authentication import get_current_user

router = APIRouter(prefix="/api/v1/simulator", tags=["Live Simulator"])

@router.post("/trigger", response_model=Dict[str, Any])
def trigger_simulated_transaction(
    force_fraud: bool = Query(False, description="Force high-risk fraudulent transaction injection"),
    count: int = Query(1, ge=1, le=50, description="Number of transactions to generate"),
    current_user: dict = Depends(get_current_user)
):
    """Generates and evaluates 1 or more synthetic transactions."""
    results = []
    for _ in range(count):
        res = simulator.generate_single_transaction(force_fraud=force_fraud)
        results.append(res)
        
    return {
        "status": "SUCCESS",
        "count": len(results),
        "results": results
    }

@router.post("/toggle", response_model=Dict[str, Any])
def toggle_continuous_stream(
    active: bool = Query(..., description="Start (true) or Stop (false) continuous stream"),
    interval_seconds: float = Query(3.0, ge=1.0, le=30.0),
    current_user: dict = Depends(get_current_user)
):
    """Starts or stops the continuous real-time background simulation."""
    if active:
        simulator.start_background_stream(interval=interval_seconds)
    else:
        simulator.stop_background_stream()
        
    return {
        "is_running": simulator.is_running,
        "interval_seconds": simulator.interval_seconds,
        "total_generated": simulator.total_generated
    }

@router.get("/status", response_model=Dict[str, Any])
def get_simulation_status(current_user: dict = Depends(get_current_user)):
    return {
        "is_running": simulator.is_running,
        "interval_seconds": simulator.interval_seconds,
        "total_generated": simulator.total_generated
    }
