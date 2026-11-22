import React from 'react';
import { ShieldAlert, Shield, Wrench, GraduationCap, User } from 'lucide-react';

const roleConfig = {
  superadmin: {
    label: 'Super Admin',
    bg: 'bg-purple-100 text-purple-800 border-purple-200',
    icon: ShieldAlert,
  },
  admin: {
    label: 'Admin',
    bg: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    icon: Shield,
  },
  technician: {
    label: 'Technician',
    bg: 'bg-amber-100 text-amber-800 border-amber-200',
    icon: Wrench,
  },
  faculty: {
    label: 'Faculty',
    bg: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    icon: GraduationCap,
  },
  student: {
    label: 'Student',
    bg: 'bg-sky-100 text-sky-800 border-sky-200',
    icon: User,
  },
};

const RoleBadge = ({ role, showIcon = true, size = 'sm' }) => {
  const normRole = (role || '').toLowerCase();
  const config = roleConfig[normRole] || {
    label: role || 'User',
    bg: 'bg-slate-100 text-slate-800 border-slate-200',
    icon: User,
  };
  const Icon = config.icon;

  const sizeClasses = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-2.5 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full border ${config.bg} ${
        sizeClasses[size] || sizeClasses.sm
      }`}
    >
      {showIcon && <Icon className="w-3.5 h-3.5" />}
      <span>{config.label}</span>
    </span>
  );
};

export default RoleBadge;
