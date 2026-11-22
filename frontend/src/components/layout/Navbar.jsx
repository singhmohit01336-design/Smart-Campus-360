import React from 'react';
import { useAuth } from '../../context/AuthContext';
import RoleBadge from '../common/RoleBadge';
import { LogOut, Bell, Menu, GraduationCap, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

const Navbar = ({ onMobileMenuToggle }) => {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Mobile Toggle & Brand */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMobileMenuToggle}
            className="lg:hidden p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
            aria-label="Toggle Navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-800 flex items-center justify-center text-white shadow-md shadow-indigo-100">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-slate-900 text-lg tracking-tight">SmartCampus</span>
                <span className="font-extrabold text-indigo-600 text-lg">360</span>
              </div>
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block -mt-1">
                Campus Intelligence & Helpdesk
              </span>
            </div>
          </Link>
        </div>

        {/* Right: Quick Actions & Profile */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center bg-indigo-50/70 border border-indigo-100 px-3 py-1 rounded-full text-xs font-medium text-indigo-700 gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            <span>AI SLA Engine Active</span>
          </div>

          {/* User Profile snippet */}
          {user && (
            <div className="flex items-center gap-3 pl-2 sm:border-l border-slate-200">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-sm font-bold text-slate-800 leading-tight">
                  {user.full_name}
                </span>
                <div className="flex items-center justify-end gap-1.5 mt-0.5">
                  <span className="text-xs text-slate-500 font-mono">
                    {user.institutional_id || user.email}
                  </span>
                  <RoleBadge role={user.role} size="xs" showIcon={false} />
                </div>
              </div>

              {/* Logout Button */}
              <button
                onClick={logout}
                title="Sign out"
                className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
