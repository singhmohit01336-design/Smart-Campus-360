import React from 'react';
import { Clock, UserCheck, PlayCircle, CheckCircle2, Archive, RefreshCw } from 'lucide-react';

const statusConfig = {
  submitted: {
    label: 'Submitted',
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    icon: Clock,
  },
  assigned: {
    label: 'Assigned',
    bg: 'bg-purple-50 text-purple-700 border-purple-200',
    dot: 'bg-purple-500',
    icon: UserCheck,
  },
  in_progress: {
    label: 'In Progress',
    bg: 'bg-amber-50 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
    icon: PlayCircle,
  },
  resolved: {
    label: 'Resolved',
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    icon: CheckCircle2,
  },
  closed: {
    label: 'Closed',
    bg: 'bg-slate-100 text-slate-700 border-slate-300',
    dot: 'bg-slate-500',
    icon: Archive,
  },
  reopened: {
    label: 'Reopened',
    bg: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500',
    icon: RefreshCw,
  },
};

const StatusBadge = ({ status, showIcon = true, size = 'sm' }) => {
  const normStatus = (status || '').toLowerCase();
  const config = statusConfig[normStatus] || {
    label: status || 'Unknown',
    bg: 'bg-slate-50 text-slate-700 border-slate-200',
    dot: 'bg-slate-400',
    icon: Clock,
  };
  const Icon = config.icon;

  const sizeClasses = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${config.bg} ${
        sizeClasses[size] || sizeClasses.sm
      }`}
    >
      {showIcon && <Icon className="w-3.5 h-3.5" />}
      <span>{config.label}</span>
    </span>
  );
};

export default StatusBadge;
