import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Ticket,
  PlusCircle,
  QrCode,
  BookOpen,
  BarChart3,
  Clock,
  Sparkles,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';

const Sidebar = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const role = (user?.role || '').toLowerCase();
  const isAdminOrSuper = role === 'admin' || role === 'superadmin';
  const isTechnician = role === 'technician';

  const navItemClass = ({ isActive }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
      isActive
        ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
    }`;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 z-40 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-16 bottom-0 left-0 z-40 w-64 bg-white border-r border-slate-200 flex flex-col justify-between transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 space-y-6 overflow-y-auto">
          {/* Main Navigation */}
          <div>
            <p className="px-3.5 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Core Operations
            </p>
            <nav className="space-y-1">
              <NavLink to="/" end className={navItemClass} onClick={onClose}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </NavLink>

              <NavLink to="/tickets" end className={navItemClass} onClick={onClose}>
                <Ticket className="w-4 h-4" />
                <span>Helpdesk Tickets</span>
              </NavLink>

              <NavLink to="/tickets/new" className={navItemClass} onClick={onClose}>
                <PlusCircle className="w-4 h-4" />
                <span>File Complaint</span>
              </NavLink>

              <NavLink to="/qr" className={navItemClass} onClick={onClose}>
                <QrCode className="w-4 h-4" />
                <span>QR Classroom Scan</span>
              </NavLink>
            </nav>
          </div>

          {/* Intelligence & Resources */}
          <div>
            <p className="px-3.5 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Campus Resources
            </p>
            <nav className="space-y-1">
              <NavLink to="/knowledge-base" className={navItemClass} onClick={onClose}>
                <BookOpen className="w-4 h-4" />
                <span>Knowledge Base</span>
              </NavLink>
            </nav>
          </div>

          {/* Management & Analytics (Admin / Superadmin only) */}
          {isAdminOrSuper && (
            <div>
              <p className="px-3.5 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Administration & Intelligence
              </p>
              <nav className="space-y-1">
                <NavLink to="/analytics" className={navItemClass} onClick={onClose}>
                  <BarChart3 className="w-4 h-4" />
                  <span>Campus Analytics</span>
                </NavLink>

                <NavLink to="/sla" className={navItemClass} onClick={onClose}>
                  <Clock className="w-4 h-4" />
                  <span>SLA Health Monitor</span>
                </NavLink>
              </nav>
            </div>
          )}

          {/* Technician Specific Notice */}
          {isTechnician && (
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900">
              <div className="flex items-center gap-1.5 font-bold mb-1">
                <UserCheck className="w-4 h-4 text-amber-600" />
                <span>Technician Dispatch</span>
              </div>
              <p className="text-amber-700 leading-relaxed">
                Check tickets assigned to you with tight SLA turnaround windows.
              </p>
            </div>
          )}
        </div>

        {/* Footer info badge */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <ShieldCheck className="w-4 h-4 text-indigo-500" />
            <span>SmartCampus v1.0 • Enterprise RBAC</span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
