import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import StatusBadge from '../../components/common/StatusBadge';
import PriorityBadge from '../../components/common/PriorityBadge';
import RoleBadge from '../../components/common/RoleBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import {
  ArrowLeft,
  Clock,
  MapPin,
  Calendar,
  User,
  Wrench,
  Paperclip,
  Send,
  MessageSquare,
  History,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Upload,
  Download,
  PlayCircle,
  RotateCcw,
  UserCheck,
} from 'lucide-react';

const TicketDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Comments state
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  // Attachment state
  const [attachments, setAttachments] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // History state
  const [history, setHistory] = useState([]);

  // Workflow actions
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Admin assign state
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [technicians, setTechnicians] = useState([]);
  const [selectedTechId, setSelectedTechId] = useState('');

  const role = (user?.role || '').toLowerCase();
  // Technicians, Admins, and Superadmins can access internal notes; Faculty and Students cannot
  const canSeeInternalNotes = ['technician', 'admin', 'superadmin'].includes(role);
  const isAdmin = ['admin', 'superadmin'].includes(role);

  const fetchTicketDetails = async () => {
    try {
      const [ticketRes, commentsRes, attachmentsRes, historyRes] = await Promise.allSettled([
        api.get(`/tickets/${id}`),
        api.get(`/tickets/${id}/comments/`),
        api.get(`/tickets/${id}/attachments/`),
        api.get(`/tickets/${id}/history`),
      ]);

      if (ticketRes.status === 'fulfilled') {
        setTicket(ticketRes.value.data);
      } else {
        throw ticketRes.reason;
      }

      if (commentsRes.status === 'fulfilled') {
        setComments(commentsRes.value.data || []);
      } else {
        setComments([]);
      }

      if (attachmentsRes.status === 'fulfilled') {
        setAttachments(attachmentsRes.value.data || []);
      } else {
        setAttachments([]);
      }

      if (historyRes.status === 'fulfilled') {
        setHistory(historyRes.value.data || []);
      } else {
        setHistory([]);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to load ticket details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTicketDetails();
  }, [id]);

  // Load technicians if admin
  useEffect(() => {
    if (isAdmin) {
      api.get('/technicians/').then((res) => {
        setTechnicians(res.data || []);
      }).catch(console.error);
    }
  }, [isAdmin]);

  // Handle Comment Submission
  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setCommentSubmitting(true);
    try {
      const res = await api.post(`/tickets/${id}/comments/`, {
        comment: newComment.trim(),
        is_internal: isInternal,
      });
      setComments((prev) => [...prev, res.data]);
      setNewComment('');
      setIsInternal(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to post comment.');
    } finally {
      setCommentSubmitting(false);
    }
  };

  // Handle File Upload
  const handleUploadAttachment = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const res = await api.post(`/tickets/${id}/attachments/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      // Refresh ticket details to include attachment
      await fetchTicketDetails();
      setUploadFile(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to upload attachment.');
    } finally {
      setUploading(false);
    }
  };

  // Handle Status Update
  const handleExecuteStatusUpdate = async () => {
    if (!targetStatus) return;
    setActionLoading(true);
    try {
      await api.patch(`/tickets/${id}/status`, {
        status: targetStatus,
        remarks: resolutionNotes || undefined,
      });
      setStatusModalOpen(false);
      setTargetStatus('');
      setResolutionNotes('');
      await fetchTicketDetails();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update ticket status.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Admin Assign
  const handleAssignTechnician = async () => {
    if (!selectedTechId) return;
    setActionLoading(true);
    try {
      await api.patch(`/tickets/${id}/assign`, {
        technician_id: parseInt(selectedTechId, 10),
      });
      setAssignModalOpen(false);
      await fetchTicketDetails();
    } catch (err) {
      alert(err.response?.data?.detail || 'Assignment failed.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading ticket details..." />;
  }

  if (error || !ticket) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded-2xl border border-slate-200 text-center">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-900 mb-1">Ticket Unavailable</h2>
        <p className="text-sm text-slate-500 mb-4">{error || 'Ticket not found or unauthorized'}</p>
        <Link
          to="/tickets"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Tickets</span>
        </Link>
      </div>
    );
  }

  const isOverdue = ticket.sla_deadline && new Date(ticket.sla_deadline) < new Date() && !['resolved', 'closed'].includes(ticket.status);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top back navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/tickets')}
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-slate-800 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Complaints</span>
        </button>

        <span className="font-mono text-xs font-bold text-slate-400">
          ID: #{ticket.id}
        </span>
      </div>

      {/* Ticket Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">
                {ticket.ticket_number}
              </span>
              <PriorityBadge priority={ticket.priority} />
              <StatusBadge status={ticket.status} />
              {ticket.qr_identifier && (
                <span className="font-mono text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                  QR: {ticket.qr_identifier}
                </span>
              )}
            </div>

            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
              {ticket.title}
            </h1>
          </div>

          {/* Workflow Action Bar */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Technician controls */}
            {role === 'technician' && ticket.status === 'assigned' && (
              <button
                onClick={() => {
                  setTargetStatus('in_progress');
                  handleExecuteStatusUpdate();
                }}
                disabled={actionLoading}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
              >
                <PlayCircle className="w-4 h-4" />
                <span>Start Working</span>
              </button>
            )}

            {role === 'technician' && ticket.status === 'in_progress' && (
              <button
                onClick={() => {
                  setTargetStatus('resolved');
                  setStatusModalOpen(true);
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Mark as Resolved</span>
              </button>
            )}

            {/* Student & Faculty controls */}
            {['student', 'faculty'].includes(role) && ticket.status === 'resolved' && (
              <>
                <button
                  onClick={() => {
                    setTargetStatus('closed');
                    handleExecuteStatusUpdate();
                  }}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Confirm & Close</span>
                </button>
                <button
                  onClick={() => {
                    setTargetStatus('reopened');
                    setStatusModalOpen(true);
                  }}
                  className="px-4 py-2 bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 rounded-xl text-xs font-bold transition flex items-center gap-1.5"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reopen Complaint</span>
                </button>
              </>
            )}

            {/* Admin Assign Button */}
            {isAdmin && (
              <button
                onClick={() => {
                  setSelectedTechId(technicians[0]?.id?.toString() || '');
                  setAssignModalOpen(true);
                }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
              >
                <UserCheck className="w-4 h-4" />
                <span>{ticket.assigned_to_id ? 'Reassign Tech' : 'Assign Tech'}</span>
              </button>
            )}
          </div>
        </div>

        {/* SLA Banner */}
        {ticket.sla_deadline && (
          <div
            className={`mt-4 p-3.5 rounded-2xl text-xs font-medium flex items-center justify-between gap-3 ${
              isOverdue
                ? 'bg-rose-50 border border-rose-200 text-rose-800'
                : 'bg-indigo-50/70 border border-indigo-100 text-indigo-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <Clock className={`w-4 h-4 ${isOverdue ? 'text-rose-600 animate-pulse' : 'text-indigo-600'}`} />
              <span>
                <strong>SLA Deadline:</strong> {new Date(ticket.sla_deadline).toLocaleString()}
              </span>
            </div>
            {isOverdue && (
              <span className="bg-rose-600 text-white font-bold px-2.5 py-0.5 rounded-full text-[10px] uppercase tracking-wider">
                Overdue Breached
              </span>
            )}
          </div>
        )}

        {/* Description Body */}
        <div className="mt-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Issue Description
          </h3>
          <p className="text-slate-800 text-sm whitespace-pre-line leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-100">
            {ticket.description}
          </p>
        </div>

        {/* Resolution Notes if Resolved */}
        {ticket.resolution_notes && (
          <div className="mt-4 p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-sm">
            <h4 className="font-bold text-xs uppercase tracking-wider text-emerald-700 mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Technician Resolution Notes</span>
            </h4>
            <p className="text-xs sm:text-sm">{ticket.resolution_notes}</p>
          </div>
        )}

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-100 text-xs">
          <div>
            <span className="text-slate-400 block font-semibold mb-0.5">Location</span>
            <div className="flex items-center gap-1 font-bold text-slate-800">
              <MapPin className="w-3.5 h-3.5 text-indigo-500" />
              <span>{ticket.building || 'Campus'} {ticket.room_number ? `Rm ${ticket.room_number}` : ''}</span>
            </div>
          </div>

          <div>
            <span className="text-slate-400 block font-semibold mb-0.5">Reported By</span>
            <div className="flex items-center gap-1 font-bold text-slate-800">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span>User #{ticket.created_by_id}</span>
            </div>
          </div>

          <div>
            <span className="text-slate-400 block font-semibold mb-0.5">Assigned Technician</span>
            <div className="flex items-center gap-1 font-bold text-slate-800">
              <Wrench className="w-3.5 h-3.5 text-amber-500" />
              <span>{ticket.assigned_to_id ? `Tech #${ticket.assigned_to_id}` : 'Unassigned'}</span>
            </div>
          </div>

          <div>
            <span className="text-slate-400 block font-semibold mb-0.5">Report Date</span>
            <div className="flex items-center gap-1 font-bold text-slate-800">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid: Comments/Attachments vs Activity History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Comments & Attachments (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Comments Thread */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-indigo-600" />
              <span>Discussion & Status Updates ({comments.length})</span>
            </h3>

            {/* Comment List */}
            <div className="space-y-4 mb-6 max-h-96 overflow-y-auto pr-2">
              {comments.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">No comments posted yet.</p>
              ) : (
                comments.map((c) => (
                  <div
                    key={c.id}
                    className={`p-4 rounded-2xl border text-xs sm:text-sm ${
                      c.is_internal
                        ? 'bg-amber-50/70 border-amber-200 text-amber-950'
                        : 'bg-slate-50 border-slate-200 text-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">
                          {c.author_name || (c.user_id ? `User #${c.user_id}` : 'User')}
                        </span>
                        {c.is_internal && (
                          <span className="inline-flex items-center gap-1 bg-amber-200/60 text-amber-900 px-2 py-0.5 rounded-full text-[10px] font-bold">
                            <Lock className="w-3 h-3" />
                            <span>Internal Staff Note</span>
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-400">
                        {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="whitespace-pre-line leading-relaxed">{c.comment || c.content}</p>
                  </div>
                ))
              )}
            </div>

            {/* Add Comment Form */}
            <form onSubmit={handleAddComment} className="space-y-3 pt-4 border-t border-slate-100">
              <textarea
                rows={3}
                required
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a message, request clarification, or update..."
                className="w-full p-3 rounded-xl border border-slate-300 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />

              <div className="flex items-center justify-between">
                {canSeeInternalNotes ? (
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-amber-800 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200">
                    <input
                      type="checkbox"
                      checked={isInternal}
                      onChange={(e) => setIsInternal(e.target.checked)}
                      className="rounded text-amber-600 focus:ring-amber-500"
                    />
                    <Lock className="w-3 h-3 text-amber-600" />
                    <span>Internal Staff Note (Hidden from Student)</span>
                  </label>
                ) : <div />}

                <button
                  type="submit"
                  disabled={commentSubmitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send Comment</span>
                </button>
              </div>
            </form>
          </div>

          {/* Attachments Section */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Paperclip className="w-4 h-4 text-indigo-600" />
              <span>Evidence & Attachments ({attachments.length})</span>
            </h3>

            {/* Existing Attachments */}
            {attachments.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
                {attachments.map((att) => (
                  <div
                    key={att.id}
                    className="p-3 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between gap-2 text-xs"
                  >
                    <div className="truncate">
                      <p className="font-bold text-slate-800 truncate">
                        {att.original_filename || att.filename}
                      </p>
                      <span className="text-[11px] text-slate-400">
                        {((att.file_size || 0) / 1024).toFixed(1)} KB
                      </span>
                    </div>
                    <a
                      href={
                        att.download_url
                          ? (att.download_url.startsWith('http')
                              ? att.download_url
                              : `http://localhost:8000${att.download_url}`)
                          : `http://localhost:8000/tickets/${ticket.id}/attachments/${att.id}/download`
                      }
                      download
                      target="_blank"
                      rel="noreferrer"
                      className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
                      title="Download file"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 mb-4">No attachments uploaded for this ticket.</p>
            )}

            {/* Upload File */}
            <form onSubmit={handleUploadAttachment} className="flex items-center gap-3">
              <input
                type="file"
                onChange={(e) => setUploadFile(e.target.files[0] || null)}
                className="text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 cursor-pointer"
              />
              <button
                type="submit"
                disabled={!uploadFile || uploading}
                className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition disabled:opacity-40 flex items-center gap-1.5 whitespace-nowrap"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Upload</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Activity History Timeline (1 col) */}
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" />
              <span>Activity Audit Trail</span>
            </h3>

            <div className="relative pl-6 space-y-5 border-l-2 border-slate-200">
              {(history || []).map((h) => (
                <div key={h.id} className="relative">
                  {/* Dot */}
                  <div className="absolute -left-[31px] top-0.5 w-3.5 h-3.5 rounded-full bg-white border-2 border-indigo-600" />
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-bold text-slate-800 capitalize">
                        {h.new_status ? `Status: ${h.new_status}` : 'Action logged'}
                        {h.changed_by_name ? ` by ${h.changed_by_name}` : ''}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 block">
                      {new Date(h.created_at).toLocaleString()}
                    </span>
                    {(h.remarks || h.comment) && (
                      <p className="text-xs text-slate-600 mt-1 bg-slate-50 p-2 rounded-lg">
                        {h.remarks || h.comment}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Status Action / Resolution / Reopen */}
      {statusModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in-95">
            <h3 className="text-lg font-bold text-slate-900 mb-2">
              {targetStatus === 'resolved' ? 'Resolve Complaint' : 'Reopen Complaint'}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              {targetStatus === 'resolved'
                ? 'Document the repair steps completed for the student.'
                : 'State why the problem persists or requires additional attention.'}
            </p>
            <textarea
              rows={4}
              required
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Provide notes or clarification..."
              className="w-full p-3 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setStatusModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteStatusUpdate}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition"
              >
                Submit Update
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Admin Technician Assign */}
      {assignModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in-95">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Assign Technician</h3>
            <p className="text-xs text-slate-500 mb-4">
              Select an available technician for ticket {ticket.ticket_number}.
            </p>
            <div className="mb-4">
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
                onClick={() => setAssignModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAssignTechnician}
                disabled={actionLoading || !selectedTechId}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition"
              >
                Save Assignment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TicketDetailPage;
