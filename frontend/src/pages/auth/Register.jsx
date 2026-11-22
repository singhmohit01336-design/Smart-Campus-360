import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GraduationCap, UserPlus, AlertCircle, CheckCircle2 } from 'lucide-react';

const Register = () => {
  const navigate = useNavigate();
  const { register, login } = useAuth();

  const [fullName, setFullName] = useState('');
  const [rollNumber, setRollNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!fullName.trim() || !rollNumber.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await register({
        fullName,
        rollNumber,
        password,
      });

      setSuccess(true);

      // Auto login immediately
      setTimeout(async () => {
        try {
          await login(rollNumber, password);
          navigate('/', { replace: true });
        } catch {
          navigate('/login');
        }
      }, 1200);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || 'Registration failed. Roll number may already be registered.'
      );
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-100 mb-3">
          <GraduationCap className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Student Portal Registration
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Create your SmartCampus 360 Student Helpdesk Account
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm border border-slate-200 rounded-3xl">
          <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-indigo-600" />
            <span>Student Registration</span>
          </h3>

          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-5 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600" />
              <span>Registration successful! Signing you in automatically...</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Alex Johnson"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                College Roll Number
              </label>
              <input
                type="text"
                required
                value={rollNumber}
                onChange={(e) => setRollNumber(e.target.value)}
                placeholder="e.g. 2024CS042"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm text-slate-900 placeholder:text-slate-400 uppercase font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Must match your official university student ID card.
              </span>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <button
              type="submit"
              disabled={loading || success}
              className="w-full mt-4 py-3 px-4 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-[0.99] transition duration-150 shadow-md shadow-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Registering Student Account...</span>
                </>
              ) : (
                <span>Complete Registration</span>
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-600">
            <span>Already have an account? </span>
            <Link
              to="/login"
              className="font-bold text-indigo-600 hover:text-indigo-700 underline"
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
