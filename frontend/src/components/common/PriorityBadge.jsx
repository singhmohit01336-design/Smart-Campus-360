import React from 'react';
import { AlertTriangle, ArrowUpRight, Minus, ArrowDownRight } from 'lucide-react';

const priorityConfig = {
  critical: {
    label: 'Critical',
    bg: 'bg-rose-50 text-rose-700 border-rose-200',
    icon: AlertTriangle,
  },
  high: {
    label: 'High',
    bg: 'bg-orange-50 text-orange-700 border-orange-200',
    icon: ArrowUpRight,
  },
  medium: {
    label: 'Medium',
    bg: 'bg-amber-50 text-amber-700 border-amber-200',
    icon: Minus,
  },
  low: {
    label: 'Low',
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: ArrowDownRight,
  },
};

const PriorityBadge = ({ priority, showIcon = true, size = 'sm' }) => {
  const normPriority = (priority || '').toLowerCase();
  const config = priorityConfig[normPriority] || {
    label: priority || 'Normal',
    bg: 'bg-slate-50 text-slate-700 border-slate-200',
    icon: Minus,
  };
  const Icon = config.icon;

  const sizeClasses = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full border ${config.bg} ${
        sizeClasses[size] || sizeClasses.sm
      }`}
    >
      {showIcon && <Icon className="w-3.5 h-3.5" />}
      <span className="capitalize">{config.label}</span>
    </span>
  );
};

export default PriorityBadge;
