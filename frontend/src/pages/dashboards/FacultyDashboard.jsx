import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import StatusBadge from '../../components/common/StatusBadge';
import PriorityBadge from '../../components/common/PriorityBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import {
  GraduationCap,
  Ticket,
  PlusCircle,
  QrCode,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

const FacultyDashboard = ({ user }) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, pending: 0, resolved: 0 });

  useEffect(() => {
    const fetchFacultyData = async () => {
      try {
        const res = await api.get('/tickets/', { params: { limit: 10 } });
        const items = res.data.items || [];
        setTickets(items);

        const total = res.data.total || items.length;
        const pending = items.filter((t) => ['submitted', 'assigned', 'in_progress'].includes(t.status)).length;
        const resolved = items.filter((t) => ['resolved', 'closed'].includes(t.status)).length;
        setStats({ total, pending, resolved });
      } catch (err) {
        console.error('Failed to load faculty tickets', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFacultyData();
  }, []);

  if (loading) {
    return <LoadingSpinner text="Loading Faculty Dashboard..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-700 to-teal-800 rounded-3xl p-6 sm:p-8 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 bg-emerald-600/50 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-emerald-100 mb-2">
            👨‍🏫 Faculty Operations
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Professor {user?.full_name}
          </h1>
          <p className="text-emerald-100 text-sm mt-1 max-w-xl">
            Report lecture hall audiovisual faults, lab infrastructure issues, or departmental maintenance with prioritized SLA.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/tickets/new"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-white text-emerald-800 font-bold text-sm shadow-md hover:bg-emerald-50 active:scale-95 transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Report Issue</span>
          </Link>
          <Link
            to="/qr"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-emerald-800/80 hover:bg-emerald-800 text-white font-bold text-sm border border-emerald-400/30 transition"
          >
            <QrCode className="w-4 h-4" />
            <span>Lecture Hall QR</span>
          </Link>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <Ticket className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Reports</span>
            <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Complaints</span>
            <p className="text-2xl font-bold text-slate-900">{stats.pending}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Resolved Issues</span>
            <p className="text-2xl font-bold text-slate-900">{stats.resolved}</p>
          </div>
        </div>
      </div>

      {/* Tickets Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Recent Departmental Issues</h2>
            <p className="text-xs text-slate-500 mt-0.5">Track classroom repairs and lab maintenance</p>
          </div>
          <Link
            to="/tickets"
            className="text-sm font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {tickets.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={Ticket}
              title="No active issues reported"
              description="Your department equipment and lecture halls have no reported issues."
              action={
                <Link
                  to="/tickets/new"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Report Equipment Issue</span>
                </Link>
              }
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {tickets.map((t) => (
              <Link
                key={t.id}
                to={`/tickets/${t.id}`}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/80 transition"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                      {t.ticket_number}
                    </span>
                    <span className="text-xs text-slate-400">
                      {t.building && `${t.building} • Rm ${t.room_number}`}
                    </span>
                  </div>
                  <h3 className="font-semibold text-slate-900 text-sm hover:text-emerald-700 transition">
                    {t.title}
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  <PriorityBadge priority={t.priority} />
                  <StatusBadge status={t.status} />
                  <ArrowRight className="w-4 h-4 text-slate-400 hidden sm:block" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FacultyDashboard;
