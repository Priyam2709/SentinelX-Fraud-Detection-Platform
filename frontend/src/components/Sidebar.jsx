import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ReceiptText, ShieldAlert, Cpu, LineChart, Network, Layers } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Executive Dashboard', icon: LayoutDashboard },
  { path: '/transactions', label: 'Transaction Explorer', icon: ReceiptText },
  { path: '/investigations', label: 'Investigation Centre', icon: ShieldAlert },
  { path: '/explainable-ai', label: 'Explainable AI & Testbench', icon: Cpu },
  { path: '/models', label: 'Model Observability', icon: LineChart },
  { path: '/network', label: 'Network Intelligence', icon: Network },
];

export default function Sidebar({ openAlertCount = 0 }) {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 flex flex-col justify-between py-6 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6 px-4">
        <div>
          <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
            Operations & Intelligence
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-cyan-500/10 text-cyan-400 font-semibold border border-cyan-500/30'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900 border border-transparent'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </div>
                  {item.path === '/investigations' && openAlertCount > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                      {openAlertCount}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Multi-Layer Engine Status Card */}
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
          <div className="flex items-center gap-2 text-slate-300 font-semibold">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Hybrid Risk Engine</span>
          </div>
          <div className="space-y-1 text-[11px] text-slate-400">
            <div className="flex justify-between">
              <span>L1: XGBoost (0.65)</span>
              <span className="text-emerald-400 font-mono">Active</span>
            </div>
            <div className="flex justify-between">
              <span>L2: Isolation Forest (0.20)</span>
              <span className="text-emerald-400 font-mono">Active</span>
            </div>
            <div className="flex justify-between">
              <span>L3: Behavioural Rules (0.15)</span>
              <span className="text-emerald-400 font-mono">Active</span>
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 text-[11px] text-slate-500 space-y-1">
        <div>SentinelX FinTech Risk Engine</div>
        <div className="text-[10px]">PyMongo 7-Collection Store</div>
      </div>
    </aside>
  );
}
