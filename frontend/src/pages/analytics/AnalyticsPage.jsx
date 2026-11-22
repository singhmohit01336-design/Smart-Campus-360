import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Users,
  Calendar,
  Sparkles,
} from 'lucide-react';

const STATUS_COLORS = {
  submitted: '#3b82f6',
  assigned: '#8b5cf6',
  in_progress: '#f59e0b',
  resolved: '#10b981',
  closed: '#64748b',
  reopened: '#f43f5e',
};

const PRIORITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#10b981',
};

const AnalyticsPage = () => {
  const [data, setData] = useState(null);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [summaryRes, techRes] = await Promise.allSettled([
          api.get('/analytics/summary'),
          api.get('/technicians/'),
        ]);
        if (summaryRes.status === 'fulfilled') {
          setData(summaryRes.value.data);
        }
        if (techRes.status === 'fulfilled') {
          setTechnicians(techRes.value.data || []);
        }
      } catch (err) {
        console.error('Failed to load analytics', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return <LoadingSpinner text="Crunching campus intelligence metrics..." />;
  }

  if (!data) {
    return <p className="text-center py-12 text-slate-500">Analytics unavailable.</p>;
  }

  // Format Status for Pie Chart: backend returns list of StatusMetric [{ status, count }]
  const statusChartData = (data.tickets_by_status || []).map((s) => ({
    name: (s.status || '').replace('_', ' ').toUpperCase(),
    value: s.count,
    color: STATUS_COLORS[s.status] || '#94a3b8',
  }));

  // Format Priority for Bar Chart: backend returns list of PriorityMetric [{ priority, count }]
  const priorityChartData = (data.tickets_by_priority || []).map((p) => ({
    name: (p.priority || '').toUpperCase(),
    count: p.count,
    color: PRIORITY_COLORS[p.priority] || '#94a3b8',
  }));

  // Daily volume: backend returns list of TrendPoint [{ date, count }]
  const dailyData = (data.ticket_trends_daily || []).map((d) => ({
    date: new Date(d.date).toLocaleDateString([], { month: 'short', day: 'numeric' }),
    count: d.count,
  }));

  // Department distribution: backend returns list of DepartmentMetric [{ department_id, department_name, count }]
  const deptData = (data.tickets_by_department || []).map((d) => ({
    name: d.department_name,
    count: d.count,
  }));

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Predictive Campus Analytics</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Campus Operations & SLA Intelligence
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time diagnostics of infrastructure faults, response efficiency, and technician throughput.
          </p>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Volume</span>
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-900">{data.total_tickets}</p>
          <span className="text-[11px] text-slate-400 mt-1 block">Campus lifetime filings</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Resolution Rate</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-emerald-600">
            {data.resolution_rate_percent ?? data.resolution_rate_pct ?? 0}%
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">
            {data.resolved_tickets} resolved of {data.total_tickets}
          </span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">SLA Compliance</span>
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-purple-600">
            {data.sla_compliance_rate_percent ?? data.sla_compliance_rate_pct ?? 100}%
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">Within targeted response window</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Avg Resolution Time</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-black text-slate-900">{data.avg_resolution_hours} hrs</p>
          <span className="text-[11px] text-slate-400 mt-1 block">Mean turnaround per issue</span>
        </div>
      </div>

      {/* Row 2: Daily Trend & Status Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Volume Trend (2 cols) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-1">Daily Complaint Influx Trend</h3>
          <p className="text-xs text-slate-500 mb-6">Volume of incident reports logged over time</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#4f46e5"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#4f46e5' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Breakdown (1 col) */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Status Distribution</h3>
            <p className="text-xs text-slate-500 mb-4">Proportion of tickets by current workflow state</p>
          </div>

          <div className="h-56 w-full flex items-center justify-center">
            {statusChartData.length === 0 ? (
              <p className="text-xs text-slate-400">No data</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {statusChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
            {statusChartData.map((s) => (
              <div key={s.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                <span className="text-slate-600 text-[11px] truncate">
                  {s.name}: <strong className="text-slate-900">{s.value}</strong>
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3: Priority Bar Chart & Department Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Bar Chart */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-1">Tickets by Priority Severity</h3>
          <p className="text-xs text-slate-500 mb-6">Distribution across urgency tiers</p>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {priorityChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Department Distribution */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-1">Complaints by Department</h3>
          <p className="text-xs text-slate-500 mb-6">Workload volume across academic & facility units</p>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={deptData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" stroke="#94a3b8" fontSize={12} tickLine={false} allowDecimals={false} />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} width={120} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 4: Technician Leaderboard */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Technician Performance & Workload</h3>
            <p className="text-xs text-slate-500 mt-0.5">Assigned work orders and resolution throughput</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 text-xs uppercase font-bold tracking-wider">
              <tr>
                <th className="py-3 px-5">Technician</th>
                <th className="py-3 px-5">Email</th>
                <th className="py-3 px-5 text-center">Institutional ID</th>
                <th className="py-3 px-5 text-center">Status</th>
                <th className="py-3 px-5 text-right">Fleet Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {technicians.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-xs text-slate-400">
                    No active technicians currently listed.
                  </td>
                </tr>
              ) : (
                technicians.map((tech) => (
                  <tr key={tech.id} className="hover:bg-slate-50 transition">
                    <td className="py-3.5 px-5 font-bold text-slate-800">
                      {tech.full_name}
                    </td>
                    <td className="py-3.5 px-5 text-xs text-slate-500">
                      {tech.email}
                    </td>
                    <td className="py-3.5 px-5 text-center">
                      <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-full">
                        {tech.institutional_id || `TECH-${tech.id}`}
                      </span>
                    </td>
                    <td className="py-3.5 px-5 text-center">
                      <span className="font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full text-xs">
                        Active Dispatch
                      </span>
                    </td>
                    <td className="py-3.5 px-5 text-right font-mono text-xs font-bold text-slate-600">
                      Campus Maintenance
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
