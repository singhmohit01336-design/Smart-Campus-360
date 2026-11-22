import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../../services/api';
import {
  PlusCircle,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  MapPin,
  Building2,
  Tag,
  ArrowRight,
  Info,
  Loader2,
} from 'lucide-react';
import PriorityBadge from '../../components/common/PriorityBadge';

const TicketCreatePage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Form State
  const [title, setTitle] = useState(searchParams.get('title') || '');
  const [description, setDescription] = useState('');
  const [departmentId, setDepartmentId] = useState(searchParams.get('department_id') || '');
  const [categoryId, setCategoryId] = useState(searchParams.get('category_id') || '');
  const [building, setBuilding] = useState(searchParams.get('building') || '');
  const [roomNumber, setRoomNumber] = useState(searchParams.get('room_number') || '');
  const [qrIdentifier, setQrIdentifier] = useState(searchParams.get('qr_identifier') || '');
  const [priority, setPriority] = useState(searchParams.get('priority') || 'medium');

  // Metadata lists
  const [departments, setDepartments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [locations, setLocations] = useState([]);

  // AI Intelligence states
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [categorySuggestion, setCategorySuggestion] = useState(null);
  const [prioritySuggestion, setPrioritySuggestion] = useState(null);
  const [aiError, setAiError] = useState('');

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Load departments, categories, and QR locations
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [deptRes, catRes, locRes] = await Promise.all([
          api.get('/departments/'),
          api.get('/categories/'),
          api.get('/qr/locations'),
        ]);
        setDepartments(deptRes.data || []);
        setCategories(catRes.data || []);
        setLocations(locRes.data || []);

        // If department is not selected yet, pick the first
        if (!departmentId && deptRes.data?.length > 0) {
          setDepartmentId(deptRes.data[0].id.toString());
        }
      } catch (err) {
        console.error('Failed to load metadata', err);
      }
    };
    loadMetadata();
  }, []);

  // Filter categories by selected department
  const filteredCategories = categories.filter(
    (c) => !departmentId || c.department_id === parseInt(departmentId, 10)
  );

  // If department changes and current category is not in filtered list, auto-select first
  useEffect(() => {
    if (filteredCategories.length > 0) {
      const match = filteredCategories.find((c) => c.id.toString() === categoryId);
      if (!match) {
        setCategoryId(filteredCategories[0].id.toString());
      }
    } else {
      setCategoryId('');
    }
  }, [departmentId, categories]);

  // Handle QR location auto-select
  const handleSelectLocation = (loc) => {
    setBuilding(loc.building);
    setRoomNumber(loc.room_number);
    setQrIdentifier(loc.qr_code_identifier || loc.qr_code);
    if (loc.department_id) {
      setDepartmentId(loc.department_id.toString());
    }
  };

  // AI Suggestion Handler
  const handleRunAiAnalysis = async () => {
    if (!title.trim() || !description.trim()) {
      setAiError('Please enter both Title and Description before requesting AI diagnosis.');
      return;
    }

    setAiAnalyzing(true);
    setAiError('');
    setCategorySuggestion(null);
    setPrioritySuggestion(null);

    try {
      const [catRes, prioRes] = await Promise.all([
        api.post('/intelligence/suggest-category', { title, description }),
        api.post('/intelligence/suggest-priority', { title, description }),
      ]);
      setCategorySuggestion(catRes.data);
      setPrioritySuggestion(prioRes.data);
    } catch (err) {
      console.error(err);
      setAiError('AI suggestion service currently unavailable.');
    } finally {
      setAiAnalyzing(false);
    }
  };

  const handleApplyAiSuggestions = () => {
    if (categorySuggestion?.suggested_category_id) {
      const targetCat = categories.find((c) => c.id === categorySuggestion.suggested_category_id);
      if (targetCat) {
        setDepartmentId(targetCat.department_id.toString());
        setCategoryId(targetCat.id.toString());
      }
    }
    if (prioritySuggestion?.suggested_priority) {
      setPriority(prioritySuggestion.suggested_priority);
    }
  };

  // Submit Complaint
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim() || !departmentId || !categoryId) {
      setError('Please complete all required fields.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const buildingStr = building.trim() || 'Main Campus';
      const roomStr = roomNumber.trim();
      const locationStr = roomStr ? `${buildingStr} - Room ${roomStr}` : buildingStr;

      const payload = {
        title: title.trim(),
        description: description.trim(),
        department_id: parseInt(departmentId, 10),
        category_id: parseInt(categoryId, 10),
        location: locationStr,
        building: buildingStr,
        room_number: roomStr || null,
        qr_code_identifier: qrIdentifier.trim() || null,
        priority: priority,
      };

      const res = await api.post('/tickets/', payload);
      navigate(`/tickets/${res.data.id}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to submit complaint.');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Submit Campus Complaint</h1>
        <p className="text-sm text-slate-500 mt-1">
          Report an equipment malfunction, infrastructure repair, or IT network grievance.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-bold text-slate-800 mb-1.5">
            Complaint Title <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Projector in CS Lab 101 display flickers intermittently"
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Description */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-sm font-bold text-slate-800">
              Detailed Description <span className="text-rose-500">*</span>
            </label>
            <button
              type="button"
              onClick={handleRunAiAnalysis}
              disabled={aiAnalyzing}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 text-xs font-bold transition border border-indigo-200 disabled:opacity-50"
            >
              {aiAnalyzing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing Issue...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  <span>AI Diagnose & Categorize</span>
                </>
              )}
            </button>
          </div>
          <textarea
            required
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Provide context, error messages, frequency of fault, and specific impact on lectures or operations..."
            className="w-full p-4 rounded-xl border border-slate-300 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {aiError && <p className="text-xs text-rose-500 mt-1">{aiError}</p>}
        </div>

        {/* AI Suggestion Box */}
        {(categorySuggestion || prioritySuggestion) && (
          <div className="bg-gradient-to-br from-indigo-50 to-slate-50 border border-indigo-200 rounded-2xl p-5 animate-in fade-in">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-indigo-600 text-white rounded-lg">
                  <Sparkles className="w-4 h-4" />
                </div>
                <h4 className="text-sm font-bold text-indigo-950">AI Campus Intelligence Recommendations</h4>
              </div>
              <button
                type="button"
                onClick={handleApplyAiSuggestions}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition shadow-sm"
              >
                Apply Recommendations
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {categorySuggestion && (
                <div className="p-3 bg-white rounded-xl border border-indigo-100 shadow-sm">
                  <span className="font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Suggested Category
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-700 text-sm">
                      {categorySuggestion.suggested_category_name}
                    </span>
                    <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-bold">
                      {Math.round(categorySuggestion.confidence_score * 100)}% match
                    </span>
                  </div>
                  <p className="text-slate-500 mt-1">{categorySuggestion.explanation}</p>
                </div>
              )}

              {prioritySuggestion && (
                <div className="p-3 bg-white rounded-xl border border-indigo-100 shadow-sm">
                  <span className="font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Suggested Priority
                  </span>
                  <div className="flex items-center justify-between">
                    <PriorityBadge priority={prioritySuggestion.suggested_priority} />
                    <span className="text-slate-400 font-mono">
                      Risk Index: {prioritySuggestion.priority_score}
                    </span>
                  </div>
                  <p className="text-slate-500 mt-1">{prioritySuggestion.reasoning}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Department & Category Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-bold text-slate-800 mb-1.5">
              Target Department <span className="text-rose-500">*</span>
            </label>
            <select
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.department_name} ({d.department_code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-800 mb-1.5">
              Issue Category <span className="text-rose-500">*</span>
            </label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {filteredCategories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.category_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-bold text-slate-800 mb-1.5">
            Initial Priority
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {['low', 'medium', 'high', 'critical'].map((p) => (
              <button
                type="button"
                key={p}
                onClick={() => setPriority(p)}
                className={`py-2 px-3 rounded-xl border text-xs font-bold capitalize transition flex items-center justify-center gap-1.5 ${
                  priority === p
                    ? 'border-indigo-600 bg-indigo-50 text-indigo-700 shadow-sm'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <PriorityBadge priority={p} showIcon={false} size="xs" />
              </button>
            ))}
          </div>
        </div>

        {/* Campus Location Details */}
        <div className="border-t border-slate-100 pt-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-indigo-600" />
              <span>Campus Incident Location</span>
            </h3>

            {locations.length > 0 && (
              <span className="text-xs text-slate-400">
                Quick pick from registered locations below
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Building Name
              </label>
              <input
                type="text"
                value={building}
                onChange={(e) => setBuilding(e.target.value)}
                placeholder="e.g. Technology Tower"
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Room Number / Lab
              </label>
              <input
                type="text"
                value={roomNumber}
                onChange={(e) => setRoomNumber(e.target.value)}
                placeholder="e.g. Lab 101 or 302"
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                QR Code Identifier
              </label>
              <input
                type="text"
                value={qrIdentifier}
                onChange={(e) => setQrIdentifier(e.target.value)}
                placeholder="e.g. QR-TECH-LAB101"
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 font-mono uppercase focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Quick select registered locations */}
          {locations.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="text-[11px] font-bold text-slate-400 self-center">Presets:</span>
              {locations.map((loc) => {
                const code = loc.qr_code_identifier || loc.qr_code;
                return (
                  <button
                    type="button"
                    key={code || loc.id}
                    onClick={() => handleSelectLocation(loc)}
                    className="px-2.5 py-1 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 transition"
                  >
                    📍 {loc.building} - {loc.room_number} ({code})
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Submit Actions */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-100 disabled:opacity-50 transition flex items-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Submitting Complaint...</span>
              </>
            ) : (
              <>
                <PlusCircle className="w-4 h-4" />
                <span>Submit Complaint</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TicketCreatePage;
