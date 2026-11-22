import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import {
  BookOpen,
  Search,
  PlusCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Tag,
  CheckCircle2,
  Trash2,
} from 'lucide-react';

const KnowledgeBasePage = () => {
  const { user } = useAuth();
  const isAdmin = ['admin', 'superadmin'].includes(user?.role?.toLowerCase());

  const [articles, setArticles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState('');

  // Expand state
  const [expandedId, setExpandedId] = useState(null);

  // Create article modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newCatId, setNewCatId] = useState('');
  const [newIsPublished, setNewIsPublished] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchArticlesAndCategories = async () => {
    try {
      const [catRes, artRes] = await Promise.all([
        api.get('/categories/'),
        api.get('/knowledge-base/', {
          params: {
            search: search.trim() || undefined,
            category_id: selectedCategoryId || undefined,
          },
        }),
      ]);
      setCategories(catRes.data || []);
      const items = artRes.data?.items ?? (Array.isArray(artRes.data) ? artRes.data : []);
      setArticles(items);
    } catch (err) {
      console.error('Failed to load KB data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticlesAndCategories();
  }, [search, selectedCategoryId]);

  const handleCreateArticle = async (e) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim() || !newCatId) return;

    setSubmitting(true);
    try {
      await api.post('/knowledge-base/', {
        title: newTitle.trim(),
        content: newContent.trim(),
        category_id: parseInt(newCatId, 10),
        is_published: newIsPublished,
      });
      setCreateModalOpen(false);
      setNewTitle('');
      setNewContent('');
      await fetchArticlesAndCategories();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create article');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteArticle = async (articleId, e) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this FAQ article?')) return;
    try {
      await api.delete(`/knowledge-base/${articleId}`);
      setArticles((prev) => prev.filter((a) => a.id !== articleId));
    } catch (err) {
      alert('Failed to delete article');
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Knowledge Base & Campus FAQs
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Self-help guides for campus WiFi, classroom technology, student portal access, and maintenance policies.
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => {
              setNewCatId(categories[0]?.id?.toString() || '');
              setCreateModalOpen(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-100 transition whitespace-nowrap"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Publish New Article</span>
          </button>
        )}
      </div>

      {/* Search & Category Pills */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search solutions: e.g. WiFi authentication, projector cable, air conditioner..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <button
            type="button"
            onClick={() => setSelectedCategoryId('')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
              selectedCategoryId === ''
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All Categories
          </button>

          {categories.map((cat) => (
            <button
              type="button"
              key={cat.id}
              onClick={() => setSelectedCategoryId(cat.id.toString())}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                selectedCategoryId === cat.id.toString()
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {cat.category_name}
            </button>
          ))}
        </div>
      </div>

      {/* Articles List / Accordion */}
      {loading ? (
        <LoadingSpinner text="Searching campus articles..." />
      ) : articles.length === 0 ? (
        <EmptyState
          icon={HelpCircle}
          title="No articles found"
          description="Try adjusting your search terms or view all categories."
        />
      ) : (
        <div className="space-y-3">
          {articles.map((art) => {
            const isExpanded = expandedId === art.id;
            return (
              <div
                key={art.id}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm transition hover:border-slate-300 overflow-hidden"
              >
                <div
                  onClick={() => setExpandedId(isExpanded ? null : art.id)}
                  className="p-5 flex items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 hover:text-indigo-600 transition">
                        {art.title}
                      </h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[11px] text-slate-400">
                          Updated {new Date(art.updated_at).toLocaleDateString()}
                        </span>
                        {!art.is_published && (
                          <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-md">
                            Draft
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {isAdmin && (
                      <button
                        onClick={(e) => handleDeleteArticle(art.id, e)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition"
                        title="Delete Article"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-5 pb-5 pt-1 text-sm text-slate-700 leading-relaxed border-t border-slate-100 bg-slate-50/50">
                    <p className="whitespace-pre-line py-3">{art.content}</p>
                    <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-400">
                      <span>Article Reference #{art.id}</span>
                      <span className="text-emerald-700 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Verified campus solution</span>
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Publish Article (Admin) */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-xl border border-slate-200 animate-in fade-in zoom-in-95">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Create Knowledge Base Article</h3>
            <p className="text-xs text-slate-500 mb-4">
              Add instructions to help students and faculty troubleshoot issues immediately.
            </p>

            <form onSubmit={handleCreateArticle} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Article Title
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. How to Connect to Campus-Secure Eduroam WiFi"
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Category
                </label>
                <select
                  value={newCatId}
                  onChange={(e) => setNewCatId(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.category_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Step-by-Step Instructions
                </label>
                <textarea
                  rows={5}
                  required
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="1. Go to WiFi Settings...&#10;2. Select SSID...&#10;3. Use college credentials..."
                  className="w-full p-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="pub"
                  checked={newIsPublished}
                  onChange={(e) => setNewIsPublished(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="pub" className="text-xs font-bold text-slate-700">
                  Publish immediately (visible to all students and faculty)
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition"
                >
                  Publish Article
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBasePage;
