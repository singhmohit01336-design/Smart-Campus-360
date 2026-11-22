import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import StatusBadge from '../../components/common/StatusBadge';
import PriorityBadge from '../../components/common/PriorityBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import {
  ShieldAlert,
  BarChart3,
  Clock,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  ArrowRight,
  Sparkles,
  Ticket,
  Users,
  RefreshCw,
} from 'lucide-react';

const AdminDashboard = ({ user }) => {
  const [tickets, setTickets] = useState([]);
  const [slaStats, setSlaStats] = useState(null);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [assigningTicketId, setAssigningTicketId] = useState(null);
  const [selectedTechId, setSelectedTechId] = useState('');
  const [assignLoading, setAssignLoading] = useState(false);
  const [slaCheckMessage, setSlaCheckMessage] = useState('');

  const fetchAdminData = async () => {
    try {
      const [ticketsRes, slaRes, techRes] = await Promise.all([
        api.get('/tickets/', { params: { limit: 10 } }),
        api.get('/sla/stats'),
        api.get('/technicians/'),
      ]);
      setTickets(ticketsRes.data.items || []);
      setSlaStats(slaRes.data);
      setTechnicians(techRes.data || []);
    } catch (err) {
      console.error('Failed to load admin dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleAssignTechnician = async (ticketId) => {
    if (!selectedTechId) return;
    setAssignLoading(true);
    try {
      await api.patch(`/tickets/${ticketId}/assign`, {
        technician_id: parseInt(selectedTechId, 10),
      });
      setAssigningTicketId(null);
      setSelectedTechId('');
      await fetchAdminData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Assignment failed');
    } finally {
      setAssignLoading(false);
    }
  };

  const handleTriggerSlaCheck = async () => {
    try {
      const res = await api.post('/sla/check');
      const evaluated = res.data.evaluated_tickets ?? 0;
      const overdue = res.data.overdue_detected ?? 0;
      setSlaCheckMessage(`SLA check complete: ${evaluated} tickets evaluated, ${overdue} overdue detected.`);
      await fetchAdminData();
      setTimeout(() => setSlaCheckMessage(''), 4000);
    } catch (err) {
      alert('SLA check failed');
    }
  };

  if (loading) {
    return <LoadingSpinner text="Aggregating campus intelligence..." />;
  }

  const unassignedTickets = tickets.filter((t) => t.status === 'submitted' || !t.assigned_to_id);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-indigo-900 rounded-3xl p-6 sm:p-8 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 bg-indigo-500/20 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-indigo-300 mb-2">
            🛡️ Administrative Control Tower
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Administrator Console
          </h1>
          <p className="text-slate-300 text-sm mt-1 max-w-xl">
            Campus-wide overview of helpdesk operations, technician assignments, SLA compliance metrics, and automated intelligence.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/analytics"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white text-indigo-950 font-bold text-xs shadow-md hover:bg-slate-100 transition"
          >
            <BarChart3 className="w-4 h-4" />
            <span>Campus Analytics</span>
          </Link>
          <button
            onClick={handleTriggerSlaCheck}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-800/80 hover:bg-indigo-700 text-white font-bold text-xs border border-indigo-500/30 transition"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Run SLA Sweep</span>
          </button>
        </div>
      </div>

      {slaCheckMessage && (
        <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-800 text-xs font-bold flex items-center gap-2 animate-in fade-in">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <span>{slaCheckMessage}</span>
        </div>
      )}

      {/* SLA Alert banner if overdue tickets exist */}
      {(slaStats?.overdue_tickets ?? slaStats?.overdue_count ?? 0) > 0 && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center flex-shrink-0 animate-pulse">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-rose-900">
                {slaStats?.overdue_tickets ?? slaStats?.overdue_count ?? 0} Overdue Campus Complaint(s) Detected
              </h4>
              <p className="text-xs text-rose-700">
                Tickets have breached SLA response thresholds. Immediate technician intervention required.
              </p>
            </div>
          </div>
          <Link
            to="/sla"
            className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition shadow-sm whitespace-nowrap"
          >
            Inspect Breaches
          </Link>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Tickets</span>
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Ticket className="w-5 h-5" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-900">{slaStats?.total_active_tickets ?? 0}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Requiring campus action</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">SLA Compliance</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <p className="text-2xl font-black text-emerald-600">
            {slaStats?.sla_compliance_rate != null
              ? `${slaStats.sla_compliance_rate}%`
              : slaStats?.sla_compliance_rate_pct != null
              ? `${slaStats.sla_compliance_rate_pct}%`
              : '100%'}
          </p>
          <span className="text-[11px] text-slate-500 mt-1 block">Resolved within SLA targets</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Overdue SLA</span>
            <div className="p-2 rounded-xl bg-rose-50 text-rose-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-2xl font-black text-rose-600">
            {slaStats?.overdue_tickets ?? slaStats?.overdue_count ?? 0}
          </p>
          <span className="text-[11px] text-slate-500 mt-1 block">Tickets past deadline</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Techs</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-900">{technicians.length}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Available for dispatch</span>
        </div>
      </div>

      {/* Unassigned Dispatch Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Unassigned Complaints Awaiting Dispatch</h2>
            <p className="text-xs text-slate-500 mt-0.5">Assign active campus technicians for swift response</p>
          </div>
          <Link
            to="/tickets"
            className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            <span>All Tickets</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {unassignedTickets.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={CheckCircle2}
              title="All tickets dispatched"
              description="No tickets currently waiting for assignment."
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {unassignedTickets.map((t) => (
              <div
                key={t.id}
                className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/60 transition"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
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
                    Location: {t.building || 'Campus'} {t.room_number ? `• Rm ${t.room_number}` : ''}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setAssigningTicketId(t.id);
                      setSelectedTechId(technicians[0]?.id?.toString() || '');
                    }}
                    className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition shadow-sm flex items-center gap-1.5"
                  >
                    <UserCheck className="w-4 h-4" />
                    <span>Assign Technician</span>
                  </button>
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

      {/* Technician Assignment Modal */}
      {assigningTicketId && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in-95">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Dispatch Campus Technician</h3>
            <p className="text-xs text-slate-500 mb-4">
              Select an available technician. The ticket status will advance to Assigned and the technician will be notified.
            </p>
            <div className="mb-4">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                Technician
              </label>
              <select
                value={selectedTechId}
                onChange={(e) => setSelectedTechId(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {technicians.map((tech) => (
                  <option key={tech.id} value={tech.id}>
                    {tech.full_name} ({tech.email})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setAssigningTicketId(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleAssignTechnician(assigningTicketId)}
                disabled={assignLoading || !selectedTechId}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition"
              >
                Confirm Assignment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
