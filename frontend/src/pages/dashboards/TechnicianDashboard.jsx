import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import StatusBadge from '../../components/common/StatusBadge';
import PriorityBadge from '../../components/common/PriorityBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import {
  Wrench,
  Clock,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
  ArrowRight,
  MapPin,
  Check,
} from 'lucide-react';

const TechnicianDashboard = ({ user }) => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ assigned: 0, inProgress: 0, resolved: 0 });
  const [resolvingTicketId, setResolvingTicketId] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchTechnicianData = async () => {
    try {
      const res = await api.get('/tickets/');
      const items = res.data.items || [];
      setTickets(items);

      const assigned = items.filter((t) => t.status === 'assigned').length;
      const inProgress = items.filter((t) => t.status === 'in_progress').length;
      const resolved = items.filter((t) => ['resolved', 'closed'].includes(t.status)).length;
      setStats({ assigned, inProgress, resolved });
    } catch (err) {
      console.error('Failed to load technician work orders', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTechnicianData();
  }, []);

  const handleUpdateStatus = async (ticketId, nextStatus, notes = '') => {
    setActionLoading(true);
    try {
      await api.patch(`/tickets/${ticketId}/status`, {
        status: nextStatus,
        resolution_notes: notes || undefined,
      });
      setResolvingTicketId(null);
      setResolutionNotes('');
      await fetchTechnicianData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update ticket status');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading technician queue..." />;
  }

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-gradient-to-r from-amber-600 to-orange-700 rounded-3xl p-6 sm:p-8 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 bg-amber-500/40 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-amber-100 mb-2">
            🔧 Maintenance & Operations Field Unit
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Technician {user?.full_name}
          </h1>
          <p className="text-amber-100 text-sm mt-1 max-w-xl">
            You have active campus work orders. Update statuses promptly to keep SLA resolution performance high.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/tickets"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-white text-orange-800 font-bold text-sm shadow-md hover:bg-orange-50 transition"
          >
            <span>Full Work Orders Queue</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Assigned to Me</span>
            <p className="text-2xl font-bold text-slate-900">{stats.assigned}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <PlayCircle className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Progress</span>
            <p className="text-2xl font-bold text-slate-900">{stats.inProgress}</p>
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

      {/* Active Work Orders */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Active Work Orders Queue</h2>
            <p className="text-xs text-slate-500 mt-0.5">Tickets assigned to your department queue</p>
          </div>
        </div>

        {tickets.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={Wrench}
              title="No work orders assigned"
              description="You have no pending tickets. New assignments will appear here."
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {tickets.map((t) => (
              <div
                key={t.id}
                className="p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:bg-slate-50/60 transition"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md">
                      {t.ticket_number}
                    </span>
                    <PriorityBadge priority={t.priority} />
                    <StatusBadge status={t.status} />
                    {t.sla_deadline && (
                      <span className="text-xs font-medium text-slate-500 flex items-center gap-1 bg-slate-100 px-2 py-0.5 rounded-md">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>SLA: {new Date(t.sla_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </span>
                    )}
                  </div>

                  <Link
                    to={`/tickets/${t.id}`}
                    className="font-bold text-slate-900 text-base hover:text-indigo-600 block transition"
                  >
                    {t.title}
                  </Link>

                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {t.building || 'Campus'} {t.room_number ? `• Rm ${t.room_number}` : ''}
                    </span>
                    <span>Created: {new Date(t.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Technician Quick Action Buttons */}
                <div className="flex items-center gap-2 self-end lg:self-center">
                  {t.status === 'assigned' && (
                    <button
                      onClick={() => handleUpdateStatus(t.id, 'in_progress')}
                      disabled={actionLoading}
                      className="px-3.5 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-bold transition shadow-sm flex items-center gap-1.5"
                    >
                      <PlayCircle className="w-4 h-4" />
                      <span>Start Work</span>
                    </button>
                  )}

                  {t.status === 'in_progress' && (
                    <button
                      onClick={() => setResolvingTicketId(t.id)}
                      disabled={actionLoading}
                      className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition shadow-sm flex items-center gap-1.5"
                    >
                      <Check className="w-4 h-4" />
                      <span>Mark Resolved</span>
                    </button>
                  )}

                  <Link
                    to={`/tickets/${t.id}`}
                    className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition"
                  >
                    Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Resolution Notes Modal */}
      {resolvingTicketId && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in-95">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Complete Ticket Resolution</h3>
            <p className="text-xs text-slate-500 mb-4">
              Describe the corrective action taken so the student and administration have clear documentation.
            </p>
            <textarea
              rows={4}
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="e.g. Replaced faulty HDMI connector and verified projection display."
              className="w-full p-3 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 mb-4"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setResolvingTicketId(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleUpdateStatus(resolvingTicketId, 'resolved', resolutionNotes)}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition"
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TechnicianDashboard;
