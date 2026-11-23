"""
SentinelX Graph Intelligence API
Provides account-to-account relationships, money mule identification, and cycle detection.
"""

from fastapi import APIRouter, Query, Depends
from typing import Dict, Any

from backend.app.services.graph_service import graph_service
from backend.app.security.authentication import get_current_user

router = APIRouter(prefix="/api/v1/graph", tags=["Network Intelligence"])

@router.get("/network", response_model=Dict[str, Any])
def get_transaction_network(
    limit: int = Query(120, ge=10, le=500),
    current_user: dict = Depends(get_current_user)
):
    limit_val = limit if isinstance(limit, int) else 120
    return graph_service.build_network_graph(limit=limit_val)
