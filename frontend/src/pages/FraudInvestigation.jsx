import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, AlertTriangle, CheckCircle2, Clock, UserPlus, 
  FileText, Check, ChevronRight, X, ShieldX, RefreshCw 
} from 'lucide-react';
import { alertAPI, investigationAPI } from '../api';
import RiskBadge from '../components/RiskBadge';

const STATUS_TABS = ['ALL', 'OPEN', 'UNDER_REVIEW', 'RESOLVED'];

export default function FraudInvestigation({ refreshTrigger }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  
  // Resolution Modal State
  const [activeAlertForResolve, setActiveAlertForResolve] = useState(null);
  const [decision, setDecision] = useState('CONFIRMED_FRAUD');
  const [remarks, setRemarks] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [selectedStatus, refreshTrigger]);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = { limit: 50 };
      if (selectedStatus !== 'ALL') params.status_filter = selectedStatus;
      const res = await alertAPI.list(params);
      setAlerts(res.alerts || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAssign = async (alertId, analyst) => {
    try {
      await alertAPI.assign(alertId, analyst);
      fetchAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpdateStatus = async (alertId, nextStatus) => {
    try {
      await alertAPI.updateStatus(alertId, nextStatus, 'Status changed from Investigation Centre');
      fetchAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!activeAlertForResolve) return;
    setIsSubmitting(true);
    try {
      await investigationAPI.create({
        alert_id: activeAlertForResolve.alert_id,
        analyst_id: 'USR_101',
        decision,
        remarks: remarks || `Investigated and verified as ${decision.toLowerCase().replace('_', ' ')}.`
      });
      setActiveAlertForResolve(null);
      setRemarks('');
      fetchAlerts();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Fraud Investigation Centre</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Triage prioritized alerts, assign cases to analysts, record forensic notes, and document confirmed fraud.
          </p>
        </div>
        <button
          onClick={fetchAlerts}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white flex items-center gap-1.5 w-fit disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          <span>{loading ? "Refreshing..." : "Refresh Queue"}</span>
        </button>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedStatus(tab)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              selectedStatus === tab
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            {tab.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Alerts Grid / Cards */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-cyan-400" />
            Loading fraud alerts...
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 text-slate-400">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-white">Queue Cleared</p>
            <p className="text-xs text-slate-400 mt-1">No alerts matching the selected status.</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.alert_id}
              className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700/80 transition-all shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
            >
              {/* Left Column: Severity, Alert ID, Reasons */}
              <div className="space-y-2 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <RiskBadge level={alert.severity} size="sm" />
                  <span className="font-mono font-bold text-sm text-white">{alert.alert_id}</span>
                  <span className="text-xs text-slate-400">• Linked to Txn: <span className="font-mono text-cyan-300">{alert.transaction_id}</span></span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    alert.status === 'OPEN' 
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                      : alert.status === 'UNDER_REVIEW'
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  }`}>
                    {alert.status.replace('_', ' ')}
                  </span>
                </div>

                {/* Risk Reasons */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {(alert.reason || []).map((r, i) => (
                    <span 
                      key={i}
                      className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300"
                    >
                      {r}
                    </span>
                  ))}
                </div>

                {/* Financial overview snippet */}
                {alert.transaction && (
                  <div className="text-xs text-slate-400 flex items-center gap-3 pt-1">
                    <span>Amount: <strong className="text-white font-mono">₹{Number(alert.transaction.amount).toLocaleString()}</strong></span>
                    <span>Type: <strong className="text-slate-200 font-mono">{alert.transaction.transaction_type}</strong></span>
                    <span>Origin: <span className="text-cyan-400 font-mono">{alert.transaction.origin_account}</span></span>
                  </div>
                )}
              </div>

              {/* Right Column: Actions & Assignee */}
              <div className="flex flex-col sm:flex-row items-end sm:items-center gap-3 shrink-0 w-full md:w-auto pt-3 md:pt-0 border-t md:border-t-0 border-slate-800">
                {/* Assign Analyst */}
                <div className="flex items-center gap-1.5 text-xs">
                  <span className="text-slate-400">Assigned:</span>
                  <select
                    value={alert.assigned_to || ''}
                    onChange={(e) => handleAssign(alert.alert_id, e.target.value)}
                    className="px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Unassigned</option>
                    <option value="Priyam">Priyam (Lead Analyst)</option>
                    <option value="Sarah Chen">Sarah Chen (Senior Analyst)</option>
                    <option value="Alexander Vance">Alexander Vance (Risk Director)</option>
                  </select>
                </div>

                {/* Status Toggles or Resolve Button */}
                {alert.status !== 'RESOLVED' ? (
                  <div className="flex items-center gap-2">
                    {alert.status === 'OPEN' && (
                      <button
                        onClick={() => handleUpdateStatus(alert.alert_id, 'UNDER_REVIEW')}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
                      >
                        Start Review
                      </button>
                    )}
                    <button
                      onClick={() => setActiveAlertForResolve(alert)}
                      className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-md flex items-center gap-1"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Investigate & Resolve</span>
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Decision: {alert.resolved_decision || 'RESOLVED'}</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Investigation Resolution Modal */}
      {activeAlertForResolve && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400" />
                <h3 className="text-base font-bold text-white">
                  Investigate Alert {activeAlertForResolve.alert_id}
                </h3>
              </div>
              <button 
                onClick={() => setActiveAlertForResolve(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleResolveSubmit} className="space-y-4">
              {/* Alert Summary Box */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                <div>Transaction: <span className="font-mono text-cyan-300 font-bold">{activeAlertForResolve.transaction_id}</span></div>
                <div>Severity: <span className="font-bold text-rose-400">{activeAlertForResolve.severity}</span></div>
                <div>Triggered: <span className="text-slate-300">{activeAlertForResolve.reason?.join(', ')}</span></div>
              </div>

              {/* Forensic Decision Selection */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Analyst Decision</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setDecision('CONFIRMED_FRAUD')}
                    className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition-all ${
                      decision === 'CONFIRMED_FRAUD'
                        ? 'bg-rose-500/20 border-rose-500 text-rose-300 shadow-rose-950 shadow-md'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <ShieldX className="w-5 h-5 text-rose-400" />
                    <span>CONFIRMED FRAUD</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setDecision('LEGITIMATE_TRANSACTION')}
                    className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition-all ${
                      decision === 'LEGITIMATE_TRANSACTION'
                        ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-emerald-950 shadow-md'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <span>LEGITIMATE TXN</span>
                  </button>
                </div>
              </div>

              {/* Case Remarks */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Case Findings & Forensic Notes</label>
                <textarea
                  rows="3"
                  placeholder="Record investigation rationale (e.g. out-of-band customer verification, IP geo-mismatch, account takeover pattern)..."
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                ></textarea>
              </div>

              {/* Modal Buttons */}
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setActiveAlertForResolve(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"
                >
                  <span>Submit & Close Alert</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
