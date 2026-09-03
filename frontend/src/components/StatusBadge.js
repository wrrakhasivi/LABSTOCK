import React from 'react';
import { AlertTriangle, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

const MAP = {
  critical: { label: 'KRITIS', cls: 'bg-red-600 text-white ring-1 ring-red-700/30', Icon: AlertTriangle },
  warning: { label: 'WASPADA', cls: 'bg-amber-500 text-slate-950 ring-1 ring-amber-600/30', Icon: AlertCircle },
  safe: { label: 'AMAN', cls: 'bg-emerald-600 text-white ring-1 ring-emerald-700/30', Icon: CheckCircle2 },
  unknown: { label: 'PERLU CEK', cls: 'bg-slate-200 text-slate-800 ring-1 ring-slate-300 dark:bg-slate-700 dark:text-slate-100 dark:ring-slate-600', Icon: HelpCircle },
};

export const StatusBadge = ({ status, className = '' }) => {
  const m = MAP[status] || MAP.unknown;
  const { Icon } = m;
  return (
    <span
      data-testid="reagen-status-badge"
      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ${m.cls} ${className}`}
    >
      <Icon className="h-3 w-3" />
      {m.label}
    </span>
  );
};
