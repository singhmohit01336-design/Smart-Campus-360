import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GraduationCap, LogIn, AlertCircle, Sparkles, KeyRound, UserCheck } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier || !password) {
      setError('Please provide your Roll Number / Email and password.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await login(identifier, password);
      navigate(from, { replace: true });
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || 'Invalid credentials. Please verify your details.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDemoFill = (demoId, demoRole) => {
    setIdentifier(demoId);
    setPassword('CampusDemo2026!#');
    setError('');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-100 mb-3">
          <GraduationCap className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          SmartCampus <span className="text-indigo-600">360</span>
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Campus Intelligence & Student Helpdesk Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm border border-slate-200 rounded-3xl">
          <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
            <LogIn className="w-5 h-5 text-indigo-600" />
            <span>Sign in to your account</span>
          </h3>

          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                College Roll No / Institutional ID / Email
              </label>
              <input
                type="text"
                required
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="e.g. 2024CS001 or admin@smartcampus360.edu"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-semibold text-slate-700">
                  Password
                </label>
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-[0.99] transition duration-150 shadow-md shadow-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Verifying credentials...</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Switcher */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex items-center gap-1.5 mb-3">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Quick Demo Accounts (1-Click Fill)
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleDemoFill('2024CS001', 'Student')}
                className="p-2 text-left rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/50 transition font-medium text-slate-700"
              >
                🎓 Student <span className="block text-[10px] text-slate-400">2024CS001</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill('FAC-001', 'Faculty')}
                className="p-2 text-left rounded-lg border border-slate-200 hover:border-emerald-400 hover:bg-emerald-50/50 transition font-medium text-slate-700"
              >
                👨‍🏫 Faculty <span className="block text-[10px] text-slate-400">FAC-001</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill('TECH-001', 'Technician')}
                className="p-2 text-left rounded-lg border border-slate-200 hover:border-amber-400 hover:bg-amber-50/50 transition font-medium text-slate-700"
              >
                🔧 Technician <span className="block text-[10px] text-slate-400">TECH-001</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill('ADM-001', 'Admin')}
                className="p-2 text-left rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/50 transition font-medium text-slate-700"
              >
                🛡️ Admin <span className="block text-[10px] text-slate-400">ADM-001</span>
              </button>
            </div>
            <button
              type="button"
              onClick={() => handleDemoFill('SA-001', 'Superadmin')}
              className="mt-2 w-full p-2 text-center rounded-lg border border-purple-200 bg-purple-50/50 hover:bg-purple-100 transition text-xs font-semibold text-purple-800"
            >
              ⚡ Superadmin Demo Account (SA-001)
            </button>
          </div>

          <div className="mt-6 text-center text-sm text-slate-600">
            <span>Don't have an account? </span>
            <Link
              to="/register"
              className="font-bold text-indigo-600 hover:text-indigo-700 underline"
            >
              Register as Student
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
