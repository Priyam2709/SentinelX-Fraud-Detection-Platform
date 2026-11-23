import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Search, Filter, ArrowUpDown, ChevronRight, X, AlertCircle, 
  Layers, User, Clock, ArrowRight, ExternalLink, RefreshCw 
} from 'lucide-react';
import { transactionAPI } from '../api';
import RiskBadge from '../components/RiskBadge';

const TYPES = ['ALL', 'TRANSFER', 'CASH_OUT', 'PAYMENT', 'CASH_IN', 'DEBIT'];
const RISK_LEVELS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export default function TransactionExplorer({ refreshTrigger }) {
  const [searchParams] = useSearchParams();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedRisk, setSelectedRisk] = useState('ALL');
  const [minAmount, setMinAmount] = useState('');
  
  // Selected Transaction for Drawer / Deep-Dive
  const [selectedTxn, setSelectedTxn] = useState(null);
  const [inspectLoading, setInspectLoading] = useState(false);

  useEffect(() => {
    fetchTransactions();
  }, [selectedType, selectedRisk, refreshTrigger]);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params = { limit: 50 };
      if (searchTerm) params.search = searchTerm;
      if (selectedType !== 'ALL') params.txn_type = selectedType;
      if (selectedRisk !== 'ALL') params.risk_level = selectedRisk;
      if (minAmount) params.min_amount = parseFloat(minAmount);

      const res = await transactionAPI.list(params);
      setTransactions(res.transactions || []);
      
      // If search matched an exact ID, automatically open inspect drawer
      if (searchTerm && res.transactions?.length === 1) {
        inspectTransaction(res.transactions[0].transaction_id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTransactions();
  };

  const inspectTransaction = async (txnId) => {
    setInspectLoading(true);
    try {
      const data = await transactionAPI.getById(txnId);
      setSelectedTxn(data);
    } catch (e) {
      console.error("Inspect error:", e);
    } finally {
      setInspectLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Transaction Explorer</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Inspect incoming financial streams, query compound MongoDB indexes, and view feature-level SHAP explanations.
          </p>
        </div>
        <button
          onClick={fetchTransactions}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white flex items-center gap-1.5 transition-colors self-start md:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          <span>{loading ? "Refreshing..." : "Refresh"}</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Transaction ID, sender (ACC_...), or recipient..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Amount Filter */}
          <div className="w-full md:w-44">
            <input
              type="number"
              placeholder="Min Amount (₹)"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <button
            type="submit"
            className="w-full md:w-auto px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-1.5"
          >
            <span>Apply Filters</span>
          </button>
        </form>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/60 text-xs">
          {/* Type filters */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <span className="text-slate-400 font-medium text-[11px] mr-1">Type:</span>
            {TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                  selectedType === t
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Risk filters */}
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-medium text-[11px] mr-1">Risk:</span>
            {RISK_LEVELS.map((r) => (
              <button
                key={r}
                onClick={() => setSelectedRisk(r)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                  selectedRisk === r
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Transactions Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase tracking-wider text-slate-400 bg-slate-800/50">
              <tr>
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Origin Sender</th>
                <th className="py-3 px-4">Destination Account</th>
                <th className="py-3 px-4">Risk Evaluation</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-12 text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-cyan-400" />
                    Querying MongoDB transactions collection...
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-12 text-slate-400">
                    No transactions matching your criteria. Try adjusting your search or filters.
                  </td>
                </tr>
              ) : (
                transactions.map((txn) => (
                  <tr 
                    key={txn.transaction_id}
                    onClick={() => inspectTransaction(txn.transaction_id)}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-cyan-300">
                      {txn.transaction_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] font-semibold border border-slate-700">
                        {txn.transaction_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      ₹{Number(txn.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      <div>{txn.origin_account}</div>
                      <div className="text-[10px] text-slate-500">
                        ₹{Number(txn.old_balance_origin).toLocaleString()} → ₹{Number(txn.new_balance_origin).toLocaleString()}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      <div>{txn.destination_account}</div>
                      <div className="text-[10px] text-slate-500">
                        Init Bal: ₹{Number(txn.old_balance_destination).toLocaleString()}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge level={txn.risk_level} score={txn.final_risk_score} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button className="text-cyan-400 group-hover:text-cyan-300 text-xs font-semibold inline-flex items-center gap-1">
                        <span>Inspect</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deep-Dive Inspection Modal / Drawer */}
      {selectedTxn && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl animate-in slide-in-from-right duration-200">
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white font-mono">{selectedTxn.transaction?.transaction_id}</h3>
                  <RiskBadge 
                    level={selectedTxn.prediction?.risk_level} 
                    score={selectedTxn.prediction?.final_risk_score} 
                    size="lg"
                  />
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Evaluated at {selectedTxn.transaction?.created_at}
                </p>
              </div>
              <button 
                onClick={() => setSelectedTxn(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Recommended Action Banner */}
            <div className={`p-3.5 rounded-xl border text-xs font-semibold flex items-center justify-between ${
              selectedTxn.prediction?.risk_level === 'CRITICAL'
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                : selectedTxn.prediction?.risk_level === 'HIGH'
                ? 'bg-orange-500/10 border-orange-500/30 text-orange-300'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            }`}>
              <span>Recommended Action: {selectedTxn.prediction?.recommended_action}</span>
              <span className="font-mono text-[11px] opacity-80">
                Latency: {selectedTxn.prediction?.prediction_time_ms}ms
              </span>
            </div>

            {/* 3-Layer Hybrid Risk Score Breakdown */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>3-Layer Risk Calibration Formula (R = 0.65P + 0.20A + 0.15B)</span>
              </h4>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">XGBoost Supervised (P)</div>
                  <div className="text-base font-extrabold text-cyan-400 font-mono mt-0.5">
                    {((selectedTxn.prediction?.fraud_probability || 0) * 100).toFixed(1)}%
                  </div>
                  <div className="text-[9px] text-slate-500">Weight: 65%</div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Isolation Forest (A)</div>
                  <div className="text-base font-extrabold text-amber-400 font-mono mt-0.5">
                    {((selectedTxn.prediction?.anomaly_score || 0) * 100).toFixed(1)}%
                  </div>
                  <div className="text-[9px] text-slate-500">Weight: 20%</div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Behavioural Engine (B)</div>
                  <div className="text-base font-extrabold text-rose-400 font-mono mt-0.5">
                    {(selectedTxn.prediction?.behavioural_score || 0).toFixed(1)}
                  </div>
                  <div className="text-[9px] text-slate-500">Weight: 15%</div>
                </div>
              </div>
            </div>

            {/* SHAP Feature Contribution Waterfall */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Explainable AI (SHAP Feature Contributions)
              </h4>
              <div className="space-y-1.5">
                {(selectedTxn.prediction?.explanations || []).map((exp, idx) => (
                  <div 
                    key={idx}
                    className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 flex items-start justify-between gap-3 text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="font-semibold text-slate-200">{exp.label}</div>
                      <div className="text-[11px] text-slate-400">{exp.summary}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={`font-mono font-bold text-xs ${
                        exp.direction === 'INCREASED_RISK' ? 'text-rose-400' : 'text-emerald-400'
                      }`}>
                        {exp.shap_value > 0 ? `+${exp.shap_value}` : exp.shap_value}
                      </span>
                      <div className="text-[10px] text-slate-500 uppercase">{exp.impact} Impact</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Financial Details */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Transaction Context</h4>
              <div className="grid grid-cols-2 gap-2 text-slate-400">
                <div>Type: <span className="font-mono text-white font-semibold">{selectedTxn.transaction?.transaction_type}</span></div>
                <div>Amount: <span className="font-mono text-white font-semibold">₹{Number(selectedTxn.transaction?.amount).toLocaleString()}</span></div>
                <div>Origin: <span className="font-mono text-cyan-300">{selectedTxn.transaction?.origin_account}</span></div>
                <div>Destination: <span className="font-mono text-cyan-300">{selectedTxn.transaction?.destination_account}</span></div>
                <div>Origin Balance Delta: <span className="font-mono text-slate-300">₹{selectedTxn.transaction?.old_balance_origin} → ₹{selectedTxn.transaction?.new_balance_origin}</span></div>
                <div>Destination Delta: <span className="font-mono text-slate-300">₹{selectedTxn.transaction?.old_balance_destination} → ₹{selectedTxn.transaction?.new_balance_destination}</span></div>
              </div>
            </div>

            {/* Customer Risk History Profile */}
            {selectedTxn.origin_customer_profile && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Sender Account Profile ({selectedTxn.origin_customer_profile.account_id})</span>
                </h4>
                <div className="grid grid-cols-2 gap-2 text-slate-400">
                  <div>Historical Txn Count: <span className="text-white font-mono">{selectedTxn.origin_customer_profile.transaction_count}</span></div>
                  <div>Average Txn Amount: <span className="text-white font-mono">₹{selectedTxn.origin_customer_profile.average_transaction_amount}</span></div>
                  <div>Previous Fraud Alerts: <span className="text-rose-400 font-mono font-bold">{selectedTxn.origin_customer_profile.risk_history?.previous_alerts || 0}</span></div>
                  <div>Confirmed Fraud Cases: <span className="text-rose-400 font-mono font-bold">{selectedTxn.origin_customer_profile.risk_history?.confirmed_fraud_cases || 0}</span></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
