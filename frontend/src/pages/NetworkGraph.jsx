import React, { useState, useEffect } from 'react';
import { 
  Network, AlertOctagon, Repeat, ShieldAlert, ArrowRight, 
  Users, RefreshCw, ZoomIn, ZoomOut, CheckCircle2 
} from 'lucide-react';
import { graphAPI } from '../api';

export default function NetworkGraph() {
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGraphData();
  }, []);

  const fetchGraphData = async () => {
    setLoading(true);
    try {
      const data = await graphAPI.getNetwork(150);
      setGraphData(data);
      if (data.nodes?.length > 0) {
        setSelectedNode(data.nodes[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const summary = graphData?.summary || {
    total_accounts: 0,
    total_edges: 0,
    detected_rings_count: 0,
    detected_mules_count: 0
  };

  const rings = graphData?.detected_rings || [];
  const mules = graphData?.mule_candidates || [];
  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Network className="w-6 h-6 text-cyan-400" />
            <span>Transaction Network Intelligence</span>
          </h2>
          <p className="text-slate-400 text-sm mt-0.5">
            NetworkX graph topology analysis identifying money mule syndicates, intermediary dispersion hubs, and circular fund laundering rings.
          </p>
        </div>
        <button
          onClick={fetchGraphData}
          className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white flex items-center gap-1.5 w-fit"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Re-compute Graph Topology</span>
        </button>
      </div>

      {/* Network Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Monitored Accounts</span>
          <div className="text-2xl font-extrabold text-white font-mono mt-1">{summary.total_accounts}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Unique graph vertices</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Transaction Edges</span>
          <div className="text-2xl font-extrabold text-cyan-400 font-mono mt-1">{summary.total_edges}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Direct fund transfers</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/70 border border-rose-500/30">
          <span className="text-xs text-rose-400 font-medium">Laundering Rings</span>
          <div className="text-2xl font-extrabold text-rose-400 font-mono mt-1">{summary.detected_rings_count}</div>
          <div className="text-[10px] text-rose-400/80 mt-0.5">Closed circular routing cycles</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/70 border border-amber-500/30">
          <span className="text-xs text-amber-400 font-medium">Money Mule Hubs</span>
          <div className="text-2xl font-extrabold text-amber-400 font-mono mt-1">{summary.detected_mules_count}</div>
          <div className="text-[10px] text-amber-400/80 mt-0.5">High in/out degree dispersion</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Graph Canvas Visualizer (8 Cols) */}
        <div className="lg:col-span-8 p-6 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Account Topology View</span>
              <span className="text-xs text-slate-500 font-normal">(Click any node to inspect relationships)</span>
            </h3>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                <span>Suspicious / Flagged</span>
              </span>
              <span className="flex items-center gap-1.5 text-cyan-400">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
                <span>Legitimate</span>
              </span>
            </div>
          </div>

          {/* SVG Interactive Graph Simulation */}
          <div className="h-96 w-full rounded-xl bg-slate-950 border border-slate-800/80 relative overflow-hidden flex items-center justify-center p-4">
            {loading ? (
              <div className="text-slate-400 flex flex-col items-center gap-2">
                <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
                <span>Computing NetworkX directed graph layout...</span>
              </div>
            ) : nodes.length === 0 ? (
              <div className="text-slate-500">No account graph relationships detected yet.</div>
            ) : (
              <svg className="w-full h-full" viewBox="0 0 700 360">
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="7"
                    markerHeight="5"
                    refX="18"
                    refY="2.5"
                    orient="auto"
                  >
                    <polygon points="0 0, 7 2.5, 0 5" fill="#475569" />
                  </marker>
                  <marker
                    id="arrowhead-danger"
                    markerWidth="7"
                    markerHeight="5"
                    refX="18"
                    refY="2.5"
                    orient="auto"
                  >
                    <polygon points="0 0, 7 2.5, 0 5" fill="#f43f5e" />
                  </marker>
                </defs>

                {/* Edges */}
                {edges.slice(0, 40).map((edge, idx) => {
                  const sIdx = nodes.findIndex((n) => n.id === edge.source);
                  const tIdx = nodes.findIndex((n) => n.id === edge.target);
                  if (sIdx === -1 || tIdx === -1) return null;

                  // Circular coordinates
                  const total = Math.min(25, nodes.length);
                  const angleS = (sIdx % total) * ((2 * Math.PI) / total);
                  const angleT = (tIdx % total) * ((2 * Math.PI) / total);
                  const x1 = 350 + 220 * Math.cos(angleS);
                  const y1 = 180 + 130 * Math.sin(angleS);
                  const x2 = 350 + 220 * Math.cos(angleT);
                  const y2 = 180 + 130 * Math.sin(angleT);

                  return (
                    <line
                      key={`edge-${idx}`}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke={edge.is_suspicious ? '#f43f5e' : '#334155'}
                      strokeWidth={edge.is_suspicious ? 1.8 : 1}
                      strokeDasharray={edge.is_suspicious ? '3 3' : 'none'}
                      markerEnd={edge.is_suspicious ? 'url(#arrowhead-danger)' : 'url(#arrowhead)'}
                      opacity={0.7}
                    />
                  );
                })}

                {/* Nodes */}
                {nodes.slice(0, 25).map((node, idx) => {
                  const total = Math.min(25, nodes.length);
                  const angle = idx * ((2 * Math.PI) / total);
                  const cx = 350 + 220 * Math.cos(angle);
                  const cy = 180 + 130 * Math.sin(angle);
                  const isSelected = selectedNode?.id === node.id;

                  return (
                    <g 
                      key={node.id} 
                      onClick={() => setSelectedNode(node)}
                      className="cursor-pointer transition-transform hover:scale-110"
                    >
                      <circle
                        cx={cx}
                        cy={cy}
                        r={node.is_flagged ? 12 : 8}
                        fill={node.is_flagged ? '#ef4444' : '#06b6d4'}
                        stroke={isSelected ? '#ffffff' : (node.is_flagged ? '#991b1b' : '#0e7490')}
                        strokeWidth={isSelected ? 3 : 1.5}
                        className={node.is_flagged ? 'animate-pulse' : ''}
                      />
                      <text
                        x={cx}
                        y={cy + 18}
                        fill="#cbd5e1"
                        fontSize="9"
                        textAnchor="middle"
                        fontFamily="monospace"
                        fontWeight={isSelected ? 'bold' : 'normal'}
                      >
                        {node.label.length > 10 ? node.label.slice(0, 9) + '…' : node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            )}
          </div>
        </div>

        {/* Right: Selected Node Details & Detected Rings (4 Cols) */}
        <div className="lg:col-span-4 space-y-5">
          {/* Node Inspector */}
          {selectedNode ? (
            <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-bold text-white uppercase tracking-wider">Account Inspector</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  selectedNode.is_flagged ? 'bg-rose-500/20 text-rose-400' : 'bg-cyan-500/20 text-cyan-400'
                }`}>
                  {selectedNode.is_flagged ? 'FLAGGED HIGH RISK' : 'NORMAL'}
                </span>
              </div>

              <div className="font-mono text-base font-bold text-cyan-300">{selectedNode.id}</div>

              <div className="space-y-2 text-xs text-slate-300">
                <div className="flex justify-between p-2 rounded-lg bg-slate-950">
                  <span className="text-slate-400">Total Sent:</span>
                  <span className="font-mono font-bold text-white">₹{selectedNode.total_sent?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between p-2 rounded-lg bg-slate-950">
                  <span className="text-slate-400">Total Received:</span>
                  <span className="font-mono font-bold text-white">₹{selectedNode.total_recv?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between p-2 rounded-lg bg-slate-950">
                  <span className="text-slate-400">In-Degree / Out-Degree:</span>
                  <span className="font-mono font-bold text-white">{selectedNode.in_degree} In / {selectedNode.out_degree} Out</span>
                </div>
                <div className="flex justify-between p-2 rounded-lg bg-slate-950">
                  <span className="text-slate-400">Peak Fraud Risk Score:</span>
                  <span className={`font-mono font-bold ${selectedNode.max_risk >= 60 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {selectedNode.max_risk}/100
                  </span>
                </div>
              </div>
            </div>
          ) : null}

          {/* Detected Laundering Rings */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Repeat className="w-4 h-4 text-rose-400" />
              <span>Detected Circular Routing Rings ({rings.length})</span>
            </h3>

            {rings.length === 0 ? (
              <div className="text-xs text-slate-500 py-3 text-center">No circular money loops identified.</div>
            ) : (
              <div className="space-y-2">
                {rings.map((ring, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-rose-500/20 text-xs space-y-1">
                    <span className="text-[10px] font-bold text-rose-400 uppercase">Laundering Cycle #{idx + 1}</span>
                    <div className="font-mono text-slate-300 flex items-center flex-wrap gap-1 text-[11px]">
                      {ring.map((acc, aIdx) => (
                        <React.Fragment key={aIdx}>
                          <span className="text-cyan-300 font-semibold">{acc}</span>
                          <ArrowRight className="w-3 h-3 text-slate-600 inline" />
                        </React.Fragment>
                      ))}
                      <span className="text-cyan-300 font-semibold">{ring[0]}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Identified Money Mule Hubs */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Users className="w-4 h-4 text-amber-400" />
              <span>High-Dispersion Money Mule Hubs ({mules.length})</span>
            </h3>

            {mules.length === 0 ? (
              <div className="text-xs text-slate-500 py-3 text-center">No high fan-in/fan-out mule hubs detected.</div>
            ) : (
              <div className="space-y-2">
                {mules.map((mule, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-amber-500/20 text-xs space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-bold text-amber-300">{mule.account_id}</span>
                      <span className="text-[10px] text-slate-400 font-mono">₹{mule.total_flow?.toLocaleString()}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{mule.reason}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
