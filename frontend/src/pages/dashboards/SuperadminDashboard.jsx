import React from 'react';
import AdminDashboard from './AdminDashboard';
import { ShieldAlert, Server, Cpu, Activity } from 'lucide-react';

const SuperadminDashboard = ({ user }) => {
  return (
    <div className="space-y-6">
      {/* Superadmin Status Strip */}
      <div className="bg-purple-950 text-purple-200 px-5 py-3 rounded-2xl flex flex-wrap items-center justify-between gap-3 text-xs border border-purple-800 shadow-sm">
        <div className="flex items-center gap-2 font-semibold">
          <ShieldAlert className="w-4 h-4 text-purple-400" />
          <span>Root Superadmin Governance Mode Active</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>PostgreSQL 16 Engine: Operational</span>
          </span>
          <span className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            <span>FastAPI Cluster: Healthy</span>
          </span>
        </div>
      </div>

      {/* Render core administrative control tower */}
      <AdminDashboard user={user} />
    </div>
  );
};

export default SuperadminDashboard;
