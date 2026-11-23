import React from 'react';

const styles = {
  LOW: {
    bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    dot: 'bg-emerald-400',
    label: 'Low Risk'
  },
  MEDIUM: {
    bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    dot: 'bg-amber-400',
    label: 'Medium Risk'
  },
  HIGH: {
    bg: 'bg-orange-500/10 border-orange-500/30 text-orange-400',
    dot: 'bg-orange-400',
    label: 'High Risk'
  },
  CRITICAL: {
    bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400 shadow-rose-950/50 shadow-sm',
    dot: 'bg-rose-400 animate-pulse',
    label: 'Critical Risk'
  }
};

export default function RiskBadge({ level = 'LOW', score, size = 'sm' }) {
  const current = styles[level?.toUpperCase()] || styles.LOW;
  const sizeClasses = size === 'lg' ? 'px-3 py-1.5 text-sm font-semibold' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${current.dot}`}></span>
      <span>{current.label}</span>
      {score !== undefined && score !== null && (
        <span className="font-mono opacity-80 pl-1 border-l border-current/20">
          {typeof score === 'number' ? score.toFixed(1) : score}
        </span>
      )}
    </span>
  );
}
