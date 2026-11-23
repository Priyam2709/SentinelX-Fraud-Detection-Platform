"""
SentinelX Transaction Network Intelligence (NetworkX)
Analyzes account-to-account transaction graphs to detect:
- Circular money routing / smurfing rings (Cycles)
- High in-degree / high out-degree money mule hubs (Fan-out / Fan-in)
- Intermediary layering chains
"""

import networkx as nx
from typing import Dict, Any, List
from backend.app.database.connection import get_collection

class NetworkIntelligenceService:
    def build_network_graph(self, limit: int = 150) -> Dict[str, Any]:
        """
        Extracts recent transactions and builds a NetworkX graph structure.
        Detects mule accounts and circular routing patterns.
        """
        txns_col = get_collection("transactions")
        preds_col = get_collection("predictions")
        
        # Fetch transactions
        records = list(txns_col.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))
        
        # Build quick prediction risk lookup
        pred_map = {}
        for p in preds_col.find({}, {"_id": 0, "transaction_id": 1, "final_risk_score": 1, "risk_level": 1}):
            pred_map[p.get("transaction_id")] = p
            
        G = nx.DiGraph()
        
        for txn in records:
            u = txn.get("origin_account", "ACC_UNKNOWN")
            v = txn.get("destination_account", "ACC_UNKNOWN")
            amt = float(txn.get("amount", 0))
            txn_id = txn.get("transaction_id", "")
            
            p_info = pred_map.get(txn_id, {})
            risk_score = p_info.get("final_risk_score", 15.0)
            is_suspicious = risk_score >= 60.0
            
            # Add or update nodes
            if not G.has_node(u):
                G.add_node(u, type="ORIGIN", total_sent=0.0, total_recv=0.0, max_risk=risk_score, is_flagged=is_suspicious)
            if not G.has_node(v):
                G.add_node(v, type="DESTINATION", total_sent=0.0, total_recv=0.0, max_risk=risk_score, is_flagged=is_suspicious)
                
            G.nodes[u]["total_sent"] += amt
            G.nodes[u]["max_risk"] = max(G.nodes[u]["max_risk"], risk_score)
            if is_suspicious:
                G.nodes[u]["is_flagged"] = True
                
            G.nodes[v]["total_recv"] += amt
            G.nodes[v]["max_risk"] = max(G.nodes[v]["max_risk"], risk_score)
            if is_suspicious:
                G.nodes[v]["is_flagged"] = True
                
            # Add edge
            if G.has_edge(u, v):
                G[u][v]["weight"] += 1
                G[u][v]["amount"] += amt
            else:
                G.add_edge(u, v, weight=1, amount=amt, is_suspicious=is_suspicious)
                
        # Pattern Detection 1: Cycle / Laundering Rings
        detected_rings = []
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                if 2 <= len(cycle) <= 6:
                    detected_rings.append(cycle)
        except Exception:
            pass
            
        # Pattern Detection 2: Money Mule Hubs (High in-degree and high out-degree)
        mule_candidates = []
        for node in G.nodes():
            in_deg = G.in_degree(node)
            out_deg = G.out_degree(node)
            if in_deg >= 2 and out_deg >= 2:
                mule_candidates.append({
                    "account_id": node,
                    "in_degree": in_deg,
                    "out_degree": out_deg,
                    "total_flow": round(G.nodes[node]["total_sent"] + G.nodes[node]["total_recv"], 2),
                    "reason": "Rapid fund dispersion across multiple inbound/outbound counterparts"
                })
                
        # Format payload for frontend visual rendering (D3 / SVG / Canvas / Force Layout)
        nodes_data = []
        for node, attr in G.nodes(data=True):
            nodes_data.append({
                "id": node,
                "label": node,
                "type": attr.get("type", "ACCOUNT"),
                "total_sent": round(attr.get("total_sent", 0), 2),
                "total_recv": round(attr.get("total_recv", 0), 2),
                "max_risk": round(attr.get("max_risk", 10), 1),
                "is_flagged": attr.get("is_flagged", False),
                "in_degree": G.in_degree(node),
                "out_degree": G.out_degree(node)
            })
            
        edges_data = []
        for u, v, attr in G.edges(data=True):
            edges_data.append({
                "source": u,
                "target": v,
                "amount": round(attr.get("amount", 0), 2),
                "transactions_count": attr.get("weight", 1),
                "is_suspicious": attr.get("is_suspicious", False)
            })
            
        return {
            "summary": {
                "total_accounts": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "detected_rings_count": len(detected_rings),
                "detected_mules_count": len(mule_candidates),
            },
            "detected_rings": detected_rings[:5],
            "mule_candidates": mule_candidates[:5],
            "nodes": nodes_data,
            "edges": edges_data
        }

graph_service = NetworkIntelligenceService()
