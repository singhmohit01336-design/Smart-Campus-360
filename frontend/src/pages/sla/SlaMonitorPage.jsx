import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import StatusBadge from '../../components/common/StatusBadge';
import PriorityBadge from '../../components/common/PriorityBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

const SlaMonitorPage = () => {
  const [stats, setStats] = useState(null);
  const [overdueTickets, setOverdueTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [bannerMessage, setBannerMessage] = useState('');

  const fetchSlaData = async () => {
    try {
      const [statsRes, overdueRes] = await Promise.all([
        api.get('/sla/stats'),
        api.get('/sla/overdue'),
      ]);
      setStats(statsRes.data);
      setOverdueTickets(overdueRes.data || []);
    } catch (err) {
      console.error('Failed to load SLA data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSlaData();
  }, []);

  const handleRunSweep = async () => {
    setChecking(true);
    try {
      const res = await api.post('/sla/check-deadlines');
      setBannerMessage(res.data.message || 'SLA verification cycle complete');
      await fetchSlaData();
      setTimeout(() => setBannerMessage(''), 5000);
    } catch (err) {
      alert('Failed to execute SLA check');
    } finally {
      setChecking(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Checking SLA thresholds and response times..." />;
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full mb-1">
            <Clock className="w-3.5 h-3.5" />
            <span>Campus SLA Service Level Agreement Watch</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            SLA Compliance Monitor
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Monitor response deadlines, identify overdue complaints, and trigger automated compliance sweeps.
          </p>
        </div>

        <button
          onClick={handleRunSweep}
          disabled={checking}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-100 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
          <span>{checking ? 'Checking Deadlines...' : 'Run SLA Sweep Now'}</span>
        </button>
      </div>

      {bannerMessage && (
        <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs font-bold flex items-center gap-2 animate-in fade-in">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <span>{bannerMessage}</span>
        </div>
      )}

      {/* SLA Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Complaints</span>
          <p className="text-2xl font-black text-slate-900 mt-1">{stats?.total_active_tickets ?? 0}</p>
          <span className="text-[11px] text-slate-400">Under resolution</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Within SLA Target</span>
          <p className="text-2xl font-black text-emerald-600 mt-1">{stats?.within_sla_count ?? 0}</p>
          <span className="text-[11px] text-slate-400">On schedule</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Breached Overdue</span>
          <p className="text-2xl font-black text-rose-600 mt-1">{stats?.overdue_count ?? 0}</p>
          <span className="text-[11px] text-slate-400">Past target SLA</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Compliance Index</span>
          <p className="text-2xl font-black text-indigo-600 mt-1">
            {stats?.sla_compliance_rate_pct != null ? `${stats.sla_compliance_rate_pct}%` : '100%'}
          </p>
          <span className="text-[11px] text-slate-400">Target: ≥ 95%</span>
        </div>
      </div>

      {/* Overdue Tickets List */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              <span>Overdue Breaches Requiring Immediate Action</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              These tickets have exceeded their SLA resolution deadlines without closure
            </p>
          </div>
          <span className="bg-rose-100 text-rose-800 text-xs font-bold px-3 py-1 rounded-full">
            {overdueTickets.length} Breaches
          </span>
        </div>

        {overdueTickets.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={CheckCircle2}
              title="Zero SLA Breaches!"
              description="All campus tickets are currently progressing within targeted service level timeframes."
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {overdueTickets.map((t) => (
              <div
                key={t.id}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-rose-50/40 transition"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200">
                      {t.ticket_number}
                    </span>
                    <PriorityBadge priority={t.priority} />
                    <StatusBadge status={t.status} />
                  </div>
                  <Link
                    to={`/tickets/${t.id}`}
                    className="font-bold text-slate-900 text-sm hover:text-indigo-600 block transition"
                  >
                    {t.title}
                  </Link>
                  <p className="text-xs text-slate-500">
                    Location: {t.building || 'Campus'} {t.room_number ? `Rm ${t.room_number}` : ''}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[11px] text-slate-400 block">SLA Deadline Was</span>
                    <span className="font-mono text-xs font-bold text-rose-600">
                      {new Date(t.sla_deadline).toLocaleString()}
                    </span>
                  </div>

                  <Link
                    to={`/tickets/${t.id}`}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition"
                  >
                    Intervene
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SlaMonitorPage;
