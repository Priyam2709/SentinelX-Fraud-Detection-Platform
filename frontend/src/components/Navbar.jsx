import React, { useState, useEffect } from 'react';
import { Shield, Activity, Play, Square, Zap, Database, UserCheck, RefreshCw } from 'lucide-react';
import { simulatorAPI } from '../api';

export default function Navbar({ onDataRefreshed }) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState(true);

  useEffect(() => {
    checkSimulatorStatus();
    const interval = setInterval(checkSimulatorStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkSimulatorStatus = async () => {
    try {
      const data = await simulatorAPI.getStatus();
      setIsStreaming(Boolean(data?.is_running));
      setIsBackendOnline(true);
    } catch (e) {
      setIsBackendOnline(false);
    }
  };

  const handleToggleStream = async () => {
    try {
      const nextState = !isStreaming;
      setIsStreaming(nextState);
      await simulatorAPI.toggle(nextState, 2.5);
      if (onDataRefreshed) onDataRefreshed();
    } catch (e) {
      console.error(e);
    }
  };

  const handleTriggerSimulated = async (forceFraud = false) => {
    setIsGenerating(true);
    try {
      await simulatorAPI.trigger(forceFraud, 1);
      if (onDataRefreshed) onDataRefreshed();
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 px-6 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-extrabold text-lg text-white tracking-tight">
              Sentinel<span className="text-cyan-400">X</span>
            </h1>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              PROD v1.0
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">Intelligent Fraud & Risk Intelligence Platform</p>
        </div>
      </div>

      {/* Simulator Actions & Live Feeds */}
      <div className="flex items-center gap-3">
        {/* MongoDB / Backend Status */}
        {isBackendOnline ? (
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs text-slate-300">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span>MongoDB / PyMongo Engine</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/15 border border-rose-500/35 text-xs text-rose-300 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            <span className="font-medium">Backend Inactive (Port 8000)</span>
          </div>
        )}

        {/* Live Stream Toggle */}
        <button
          onClick={handleToggleStream}
          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-2 transition-all ${
            isStreaming
              ? 'bg-rose-500/20 border-rose-500/40 text-rose-300 hover:bg-rose-500/30'
              : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200'
          }`}
          title="Toggle live automated background transaction generator"
        >
          {isStreaming ? (
            <>
              <Square className="w-3.5 h-3.5 fill-current text-rose-400" />
              <span>Streaming Live</span>
              <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping"></span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current text-cyan-400" />
              <span>Start Live Stream</span>
            </>
          )}
        </button>

        {/* Generate Regular Transaction */}
        <button
          disabled={isGenerating}
          onClick={() => handleTriggerSimulated(false)}
          className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Simulate Txn</span>
        </button>

        {/* Inject Fraud Scenario */}
        <button
          disabled={isGenerating}
          onClick={() => handleTriggerSimulated(true)}
          className="px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
          title="Inject an intentional high-risk account takeover or drain transaction"
        >
          <Zap className="w-3.5 h-3.5 text-rose-400" />
          <span className="hidden md:inline">Inject Fraud Test</span>
        </button>

        {/* Analyst Profile */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-cyan-950/60 border border-cyan-700/50 flex items-center justify-center text-xs font-bold text-cyan-300">
            PR
          </div>
          <div className="hidden xl:block text-left">
            <div className="text-xs font-semibold text-slate-200 leading-tight">Priyam</div>
            <div className="text-[10px] text-cyan-400">Lead Risk Analyst</div>
          </div>
        </div>
      </div>
    </header>
  );
}
