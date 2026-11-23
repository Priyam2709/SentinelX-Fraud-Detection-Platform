import React, { useState } from 'react';
import { 
  Cpu, Sparkles, TrendingUp, AlertTriangle, CheckCircle2, 
  ArrowRight, Sliders, ShieldCheck, ShieldAlert, BarChart3, Info 
} from 'lucide-react';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Cell, ReferenceLine 
} from 'recharts';
import { riskAPI } from '../api';
import RiskBadge from '../components/RiskBadge';

export default function ExplainableAI() {
  // Testbench Input State
  const [amount, setAmount] = useState(85000);
  const [txnType, setTxnType] = useState('TRANSFER');
  const [oldBalanceOrig, setOldBalanceOrig] = useState(85000);
  const [newBalanceOrig, setNewBalanceOrig] = useState(0);
  const [oldBalanceDest, setOldBalanceDest] = useState(0);
  const [newBalanceDest, setNewBalanceDest] = useState(85000);
  
  // Quick Presets
  const [isDrained, setIsDrained] = useState(true);
  const [isNewDest, setIsNewDest] = useState(true);

  // Result State
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleDrainToggle = (e) => {
    const val = e.target.checked;
    setIsDrained(val);
    if (val) {
      setOldBalanceOrig(amount);
      setNewBalanceOrig(0);
    } else {
      setOldBalanceOrig(amount + 45000);
      setNewBalanceOrig(45000);
    }
  };

  const handleNewDestToggle = (e) => {
    const val = e.target.checked;
    setIsNewDest(val);
    if (val) {
      setOldBalanceDest(0);
      setNewBalanceDest(amount);
    } else {
      setOldBalanceDest(50000);
      setNewBalanceDest(50000 + amount);
    }
  };

  const handleRunAssessment = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        transaction_type: txnType,
        amount: parseFloat(amount),
        origin_account: 'ACC_SIM_SENDER',
        destination_account: 'ACC_SIM_RECIPIENT',
        old_balance_origin: parseFloat(oldBalanceOrig),
        new_balance_origin: parseFloat(newBalanceOrig),
        old_balance_destination: parseFloat(oldBalanceDest),
        new_balance_destination: parseFloat(newBalanceDest)
      };
      const res = await riskAPI.predict(payload, false);
      setResult(res.prediction);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Prepare SHAP chart data
  const shapData = (result?.explanations || []).map((exp) => ({
    name: exp.label.replace('Txn Type: ', ''),
    shap_value: exp.shap_value,
    direction: exp.direction,
    summary: exp.summary
  }));

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Cpu className="w-6 h-6 text-cyan-400" />
          <span>Explainable AI & Interactive Risk Testbench</span>
        </h2>
        <p className="text-slate-400 text-sm mt-0.5">
          Evaluate transaction scenarios in real time and inspect exact Tree SHAP feature contributions that drive the fraud probability.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Interactive Testbench Controls (5 Cols) */}
        <div className="lg:col-span-5 p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Scenario Parameters</span>
            </h3>
            <span className="text-[11px] text-cyan-400 font-mono">Live Simulator</span>
          </div>

          <form onSubmit={handleRunAssessment} className="space-y-4 text-xs">
            {/* Transaction Type */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Transaction Type</label>
              <select
                value={txnType}
                onChange={(e) => setTxnType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="TRANSFER">TRANSFER (High Risk Channel)</option>
                <option value="CASH_OUT">CASH_OUT (High Risk Channel)</option>
                <option value="PAYMENT">PAYMENT (Low Risk Merchant)</option>
                <option value="CASH_IN">CASH_IN (Deposit Stream)</option>
                <option value="DEBIT">DEBIT (Standard POS)</option>
              </select>
            </div>

            {/* Amount Slider & Input */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label className="font-semibold text-slate-300">Transaction Amount (₹)</label>
                <span className="font-mono text-cyan-300 font-bold">₹{Number(amount).toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="500"
                max="500000"
                step="500"
                value={amount}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setAmount(val);
                  if (isDrained) {
                    setOldBalanceOrig(val);
                    setNewBalanceOrig(0);
                  }
                  if (isNewDest) {
                    setNewBalanceDest(val);
                  }
                }}
                className="w-full accent-cyan-500 cursor-pointer"
              />
            </div>

            {/* Origin Sender Balance */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="font-medium text-slate-400 text-[11px]">Origin Prior Bal (₹)</label>
                <input
                  type="number"
                  value={oldBalanceOrig}
                  onChange={(e) => setOldBalanceOrig(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="font-medium text-slate-400 text-[11px]">Origin Post Bal (₹)</label>
                <input
                  type="number"
                  value={newBalanceOrig}
                  onChange={(e) => setNewBalanceOrig(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono"
                />
              </div>
            </div>

            {/* Quick Presets Switches */}
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-slate-300 font-medium">Account Drain Pattern (New Bal = 0)</span>
                <input
                  type="checkbox"
                  checked={isDrained}
                  onChange={handleDrainToggle}
                  className="w-4 h-4 accent-rose-500 rounded"
                />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-slate-300 font-medium">Recipient Has Zero Prior Balance</span>
                <input
                  type="checkbox"
                  checked={isNewDest}
                  onChange={handleNewDestToggle}
                  className="w-4 h-4 accent-amber-500 rounded"
                />
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-600/20 transition-all flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Evaluating Model Inferences...' : 'Run Live Risk Assessment'}</span>
            </button>
          </form>
        </div>

        {/* Right: Real-time Evaluation & SHAP Waterfall (7 Cols) */}
        <div className="lg:col-span-7 space-y-5">
          {result ? (
            <>
              {/* Score Header Card */}
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs text-slate-400 font-medium">Calibrated Hybrid Risk Score</span>
                    <div className="text-3xl font-extrabold font-mono text-white mt-0.5">
                      {result.final_risk_score} <span className="text-sm font-normal text-slate-400">/ 100</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <RiskBadge level={result.risk_level} score={result.final_risk_score} size="lg" />
                  </div>
                </div>

                {/* 3 Component Breakdown */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs pt-3 border-t border-slate-800">
                  <div className="p-2 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Supervised (65%)</div>
                    <div className="font-mono font-bold text-cyan-400 text-sm mt-0.5">
                      {(result.fraud_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Anomaly (20%)</div>
                    <div className="font-mono font-bold text-amber-400 text-sm mt-0.5">
                      {(result.anomaly_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-2 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Behavioural (15%)</div>
                    <div className="font-mono font-bold text-rose-400 text-sm mt-0.5">
                      {result.behavioural_score}
                    </div>
                  </div>
                </div>
              </div>

              {/* SHAP Waterfall Chart */}
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-cyan-400" />
                      <span>SHAP Feature Impact Waterfall</span>
                    </h3>
                    <p className="text-xs text-slate-400">
                      Positive (Red) increases fraud likelihood; Negative (Green) supports legitimate transfer.
                    </p>
                  </div>
                </div>

                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={shapData}
                      margin={{ top: 10, right: 20, left: 35, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                      <XAxis type="number" stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                      <YAxis type="category" dataKey="name" stroke="#cbd5e1" fontSize={11} width={130} />
                      <ReferenceLine x={0} stroke="#94a3b8" />
                      <Tooltip 
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const d = payload[0].payload;
                            return (
                              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs shadow-xl space-y-1">
                                <div className="font-bold text-white">{d.name}</div>
                                <div className="text-cyan-400 font-mono">Shapley Impact: {d.shap_value}</div>
                                <div className="text-slate-400 text-[11px]">{d.summary}</div>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar dataKey="shap_value" radius={[4, 4, 4, 4]}>
                        {shapData.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.shap_value > 0 ? '#ef4444' : '#10b981'} 
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Forensic Rationale Explanations */}
              <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-2">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-cyan-400" />
                  <span>AI Forensic Narrative for Analysts</span>
                </h4>
                <div className="space-y-1.5">
                  {result.explanations?.slice(0, 4).map((exp, i) => (
                    <div 
                      key={i} 
                      className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-start gap-2"
                    >
                      <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-1.5 ${
                        exp.direction === 'INCREASED_RISK' ? 'bg-rose-400' : 'bg-emerald-400'
                      }`}></span>
                      <div>
                        <strong className="text-slate-200">{exp.label}:</strong>{' '}
                        <span className="text-slate-400">{exp.summary}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="h-full min-h-[400px] rounded-2xl bg-slate-900/40 border border-slate-800 border-dashed flex flex-col items-center justify-center p-8 text-center text-slate-400 space-y-3">
              <Sliders className="w-10 h-10 text-slate-600" />
              <div>
                <p className="text-sm font-semibold text-white">No Scenario Evaluated Yet</p>
                <p className="text-xs text-slate-400 max-w-sm mt-1">
                  Adjust the scenario parameters on the left and click "Run Live Risk Assessment" to compute real-time SHAP feature explanations.
                </p>
              </div>
              <button
                onClick={() => handleRunAssessment()}
                className="px-4 py-2 rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 text-cyan-300 text-xs font-semibold"
              >
                Evaluate Default Scenario
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
