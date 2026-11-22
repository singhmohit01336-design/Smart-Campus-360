import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import StatusBadge from '../../components/common/StatusBadge';
import PriorityBadge from '../../components/common/PriorityBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import {
  Ticket,
  Search,
  Filter,
  PlusCircle,
  Clock,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  MapPin,
} from 'lucide-react';

const TicketListPage = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [tickets, setTickets] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Pagination & Filter state
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [priority, setPriority] = useState(searchParams.get('priority') || '');
  const [departmentId, setDepartmentId] = useState(searchParams.get('department_id') || '');
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10));
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const pageSize = 10;

  // Load departments & categories for filters
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [deptRes, catRes] = await Promise.all([
          api.get('/departments/'),
          api.get('/categories/'),
        ]);
        setDepartments(deptRes.data || []);
        setCategories(catRes.data || []);
      } catch (err) {
        console.error('Failed to load filter metadata', err);
      }
    };
    fetchMetadata();
  }, []);

  // Fetch tickets
  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
      };
      if (search.trim()) params.search = search.trim();
      if (status) params.status = status;
      if (priority) params.priority = priority;
      if (departmentId) params.department_id = departmentId;

      const res = await api.get('/tickets/', { params });
      setTickets(res.data.items || []);
      setTotalPages(res.data.total_pages || 1);
      setTotalCount(res.data.total || 0);
    } catch (err) {
      console.error('Failed to fetch tickets', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [page, status, priority, departmentId]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTickets();
  };

  const handleResetFilters = () => {
    setSearch('');
    setStatus('');
    setPriority('');
    setDepartmentId('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Helpdesk Complaints</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            View, track, and manage all campus service requests and maintenance reports
          </p>
        </div>

        <Link
          to="/tickets/new"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-md shadow-indigo-100 transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Submit New Complaint</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by ticket #, title, or keywords..."
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-300 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs sm:text-sm font-semibold transition"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 mr-2">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          {/* Status Select */}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="reopened">Reopened</option>
          </select>

          {/* Priority Select */}
          <select
            value={priority}
            onChange={(e) => {
              setPriority(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          {/* Department Select */}
          <select
            value={departmentId}
            onChange={(e) => {
              setDepartmentId(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Departments</option>
            {departments.map((dept) => (
              <option key={dept.id} value={dept.id}>
                {dept.department_name}
              </option>
            ))}
          </select>

          {(status || priority || departmentId || search) && (
            <button
              onClick={handleResetFilters}
              className="text-xs font-semibold text-rose-600 hover:text-rose-700 px-2 py-1"
            >
              Reset Filters
            </button>
          )}

          <div className="ml-auto text-xs text-slate-500 font-medium">
            Found <span className="font-bold text-slate-800">{totalCount}</span> tickets
          </div>
        </div>
      </div>

      {/* Ticket List View */}
      {loading ? (
        <LoadingSpinner text="Retrieving complaints list..." />
      ) : tickets.length === 0 ? (
        <EmptyState
          icon={Ticket}
          title="No complaints match your criteria"
          description="Try broadening your filters or submit a new campus complaint."
          action={
            <Link
              to="/tickets/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Complaint</span>
            </Link>
          }
        />
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 text-xs uppercase font-bold tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Ticket</th>
                  <th className="py-3.5 px-4">Issue Details</th>
                  <th className="py-3.5 px-4">Location</th>
                  <th className="py-3.5 px-4">Priority</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">SLA Target</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tickets.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-xs font-bold text-indigo-600">
                      {t.ticket_number}
                    </td>
                    <td className="py-3.5 px-4 max-w-xs sm:max-w-md">
                      <Link
                        to={`/tickets/${t.id}`}
                        className="font-bold text-slate-900 hover:text-indigo-600 line-clamp-1 transition"
                      >
                        {t.title}
                      </Link>
                      <span className="text-xs text-slate-400 block mt-0.5">
                        Filed {new Date(t.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-xs text-slate-600">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{t.building || 'Campus'} {t.room_number ? `Rm ${t.room_number}` : ''}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <PriorityBadge priority={t.priority} />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-xs">
                      {t.sla_deadline ? (
                        <span className="flex items-center gap-1 font-mono text-slate-600">
                          <Clock className="w-3 h-3 text-slate-400" />
                          {new Date(t.sla_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-right">
                      <Link
                        to={`/tickets/${t.id}`}
                        className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-800"
                      >
                        <span>View</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="p-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Page <span className="font-bold text-slate-800">{page}</span> of {totalPages}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-1.5 rounded-lg border border-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 transition"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="p-1.5 rounded-lg border border-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 transition"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TicketListPage;
