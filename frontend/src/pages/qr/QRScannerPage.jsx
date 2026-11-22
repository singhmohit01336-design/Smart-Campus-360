import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import {
  QrCode,
  MapPin,
  Building2,
  Search,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

const QRScannerPage = () => {
  const navigate = useNavigate();

  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inputCode, setInputCode] = useState('');
  const [resolvedLocation, setResolvedLocation] = useState(null);
  const [resolving, setResolving] = useState(false);
  const [resolveError, setResolveError] = useState('');

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const res = await api.get('/qr/locations');
        setLocations(res.data || []);
      } catch (err) {
        console.error('Failed to load QR locations', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, []);

  const handleLookupCode = async (codeToLookup) => {
    const code = (codeToLookup || inputCode).trim().toUpperCase();
    if (!code) return;

    setResolving(true);
    setResolveError('');
    setResolvedLocation(null);

    try {
      const res = await api.get(`/qr/${code}`);
      setResolvedLocation(res.data);
    } catch (err) {
      setResolveError(
        err.response?.data?.detail || `QR location '${code}' is not recognized in the campus database.`
      );
    } finally {
      setResolving(false);
    }
  };

  const handleProceedToReport = (loc) => {
    const params = new URLSearchParams({
      building: loc.building,
      room_number: loc.room_number,
      qr_identifier: loc.qr_code,
    });
    if (loc.department_id) {
      params.append('department_id', loc.department_id.toString());
    }
    navigate(`/tickets/new?${params.toString()}`);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full mb-1">
          <QrCode className="w-3.5 h-3.5" />
          <span>Classroom QR Geolocation System</span>
        </div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          QR Location Incident Reporting
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Scan the QR placard affixed to your classroom or lab door to report equipment faults with automatic room attribution.
        </p>
      </div>

      {/* Manual QR Lookup Bar */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-800">Scan or Enter QR Code Manually</h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleLookupCode();
          }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <div className="relative flex-1">
            <QrCode className="w-5 h-5 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              value={inputCode}
              onChange={(e) => setInputCode(e.target.value)}
              placeholder="e.g. QR-TECH-LAB101, QR-ACAD-302, QR-ENG-LH2..."
              className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={resolving || !inputCode.trim()}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {resolving ? 'Verifying...' : 'Resolve Location'}
          </button>
        </form>

        {resolveError && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{resolveError}</span>
          </div>
        )}

        {/* Resolved Location Card */}
        {resolvedLocation && (
          <div className="p-5 rounded-2xl bg-indigo-50/70 border border-indigo-200 animate-in fade-in flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-indigo-700 bg-white px-2 py-0.5 rounded-md border border-indigo-100">
                  {resolvedLocation.qr_code}
                </span>
                <span className="text-xs font-bold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Campus Verified</span>
                </span>
              </div>
              <h4 className="text-base font-black text-slate-900">
                {resolvedLocation.building} — Room {resolvedLocation.room_number}
              </h4>
              <p className="text-xs text-slate-500">{resolvedLocation.description}</p>
            </div>

            <button
              onClick={() => handleProceedToReport(resolvedLocation)}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-100 transition flex items-center justify-center gap-2 whitespace-nowrap"
            >
              <span>File Complaint in this Room</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Campus Location Directory */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Registered Campus QR Locations</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Click any campus room below to test one-click location attribution
          </p>
        </div>

        {loading ? (
          <LoadingSpinner text="Loading campus locations..." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {locations.map((loc) => (
              <div
                key={loc.qr_code}
                className="p-5 rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-sm transition bg-white flex flex-col justify-between gap-4"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
                      {loc.qr_code}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      ID #{loc.id}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-sm">
                    {loc.building} — Room {loc.room_number}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {loc.description || 'Campus academic lecture hall / facility'}
                  </p>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                  <button
                    onClick={() => handleLookupCode(loc.qr_code)}
                    className="flex-1 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                  >
                    Inspect QR
                  </button>

                  <button
                    onClick={() => handleProceedToReport(loc)}
                    className="flex-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center justify-center gap-1"
                  >
                    <span>Report Fault</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default QRScannerPage;
