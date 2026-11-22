import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import StatusBadge from '../../components/common/StatusBadge';
import PriorityBadge from '../../components/common/PriorityBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import {
  Ticket,
  Clock,
  CheckCircle2,
  PlusCircle,
  QrCode,
  BookOpen,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';

const StudentDashboard = ({ user }) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, active: 0, resolved: 0 });

  useEffect(() => {
    const fetchStudentData = async () => {
      try {
        const res = await api.get('/tickets/', { params: { limit: 10 } });
        const items = res.data.items || [];
        setTickets(items);

        const total = res.data.total || items.length;
        const active = items.filter((t) => ['submitted', 'assigned', 'in_progress'].includes(t.status)).length;
        const resolved = items.filter((t) => ['resolved', 'closed'].includes(t.status)).length;
        setStats({ total, active, resolved });
      } catch (err) {
        console.error('Failed to load tickets', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStudentData();
  }, []);

  if (loading) {
    return <LoadingSpinner text="Loading your helpdesk dashboard..." />;
  }

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 rounded-3xl p-6 sm:p-8 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 bg-indigo-500/30 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-indigo-100 mb-2">
            🎓 Student Helpdesk
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {user?.full_name}!
          </h1>
          <p className="text-indigo-100 text-sm mt-1 max-w-xl">
            Track your campus complaints, report classroom maintenance issues, or find quick answers in the knowledge base.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/tickets/new"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-white text-indigo-700 font-bold text-sm shadow-md hover:bg-indigo-50 active:scale-95 transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>File Complaint</span>
          </Link>
          <Link
            to="/qr"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-indigo-700/80 hover:bg-indigo-700 text-white font-bold text-sm border border-indigo-400/30 transition"
          >
            <QrCode className="w-4 h-4" />
            <span>QR Scan</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Ticket className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Filed</span>
            <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Progress / Active</span>
            <p className="text-2xl font-bold text-slate-900">{stats.active}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Resolved</span>
            <p className="text-2xl font-bold text-slate-900">{stats.resolved}</p>
          </div>
        </div>
      </div>

      {/* Recent Tickets Section */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">My Recent Complaints</h2>
            <p className="text-xs text-slate-500 mt-0.5">Live status updates and resolution progress</p>
          </div>
          <Link
            to="/tickets"
            className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {tickets.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={Ticket}
              title="No complaints filed yet"
              description="Everything is running smoothly! If you notice any campus issues, submit a ticket anytime."
              action={
                <Link
                  to="/tickets/new"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Submit First Complaint</span>
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
                    <span className="font-mono text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
                      {t.ticket_number}
                    </span>
                    <span className="text-xs text-slate-400">
                      {t.building && `${t.building} ${t.room_number ? '• Rm ' + t.room_number : ''}`}
                    </span>
                  </div>
                  <h3 className="font-semibold text-slate-900 text-sm hover:text-indigo-600 transition">
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

      {/* Quick Help & FAQ Banner */}
      <div className="bg-slate-100/70 border border-slate-200 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900">Need instant answers for campus WiFi or lab access?</h4>
            <p className="text-xs text-slate-500">Check our self-service Knowledge Base before submitting a ticket.</p>
          </div>
        </div>
        <Link
          to="/knowledge-base"
          className="px-4 py-2 bg-white text-indigo-700 hover:bg-indigo-50 border border-slate-200 rounded-xl text-xs font-bold transition shadow-sm whitespace-nowrap"
        >
          Browse FAQs
        </Link>
      </div>
    </div>
  );
};

export default StudentDashboard;
