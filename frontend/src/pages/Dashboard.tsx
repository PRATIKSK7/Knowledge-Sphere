import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { 
  FileText, 
  TrendingUp, 
  Network, 
  Activity, 
  ArrowUpRight, 
  RefreshCw,
  Search
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.get('/analytics/');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await api.get(`/search/semantic?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center flex-col gap-3">
        <RefreshCw className="h-8 w-8 text-blue-500 animate-spin" />
        <p className="text-slate-400 text-sm">Compiling research dashboard...</p>
      </div>
    );
  }

  // Fallbacks if data is mock/empty
  const totalDocs = data?.total_documents ?? 0;
  const totalNodes = data?.graph?.total_nodes ?? 0;
  const totalRels = data?.graph?.total_relationships ?? 0;
  const trends = data?.trending_topics ?? [];
  const activityData = data?.user_activity ?? [];

  return (
    <div className="space-y-8">
      {/* Title section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            Research Intelligence Centre
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Global metrics of parsed papers, extracted concepts, and semantic relations
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/documents"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-600/20"
          >
            <FileText className="h-4 w-4" />
            Upload Document
          </Link>
          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-2 px-4 py-2 border border-slate-800 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/40 text-sm transition-all"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh Metrics
          </button>
        </div>
      </div>

      {/* Stats counter cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center gap-5">
          <div className="p-4 bg-blue-500/10 rounded-xl text-blue-400">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <span className="block text-[11px] font-semibold text-slate-400 uppercase tracking-widest leading-none">
              Uploaded Papers
            </span>
            <span className="block text-2xl font-bold text-white mt-1.5">{totalDocs}</span>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center gap-5">
          <div className="p-4 bg-indigo-500/10 rounded-xl text-indigo-400">
            <Network className="h-6 w-6" />
          </div>
          <div>
            <span className="block text-[11px] font-semibold text-slate-400 uppercase tracking-widest leading-none">
              Extracted Nodes
            </span>
            <span className="block text-2xl font-bold text-white mt-1.5">{totalNodes}</span>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center gap-5">
          <div className="p-4 bg-emerald-500/10 rounded-xl text-emerald-400">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div>
            <span className="block text-[11px] font-semibold text-slate-400 uppercase tracking-widest leading-none">
              Graph Connections
            </span>
            <span className="block text-2xl font-bold text-white mt-1.5">{totalRels}</span>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex items-center gap-5">
          <div className="p-4 bg-violet-500/10 rounded-xl text-violet-400">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <span className="block text-[11px] font-semibold text-slate-400 uppercase tracking-widest leading-none">
              System Health
            </span>
            <span className="block text-2xl font-bold text-white mt-1.5">99.8%</span>
          </div>
        </div>
      </div>

      {/* Semantic Search Sandbox (Module 4 similarity/semantic query interface) */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h2 className="text-lg font-bold text-slate-200">Semantic Search Sandbox</h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search across thousands of parsed document chunks (e.g. attention mechanism, neural models)"
              className="w-full pl-10 pr-4 py-3 rounded-lg glass-input text-sm"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-600/20"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </form>

        {searchResults.length > 0 && (
          <div className="space-y-3 pt-3 border-t border-slate-800/60 max-h-72 overflow-y-auto">
            <p className="text-xs text-slate-400">Showing top semantic chunk matches:</p>
            {searchResults.map((res, i) => (
              <div key={i} className="glass-card p-4 rounded-xl border border-slate-800/80 space-y-1">
                <div className="flex justify-between items-center text-xs text-slate-400">
                  <span className="font-semibold text-blue-400">{res.metadata?.filename}</span>
                  <span>Confidence: {(res.confidence * 100).toFixed(1)}%</span>
                </div>
                <p className="text-xs text-slate-350 italic">"{res.content}"</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Area Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 lg:col-span-2 space-y-4">
          <h3 className="text-lg font-bold text-slate-200">Upload & Query Activity</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activityData}>
                <defs>
                  <linearGradient id="colorUploads" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorQueries" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                  labelStyle={{ color: '#94a3b8', fontSize: 11 }}
                />
                <Area type="monotone" dataKey="uploads" name="Document Uploads" stroke="#3b82f6" fillOpacity={1} fill="url(#colorUploads)" />
                <Area type="monotone" dataKey="queries" name="Agent Queries" stroke="#818cf8" fillOpacity={1} fill="url(#colorQueries)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trending topics list */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-lg font-bold text-slate-200">Trending Concepts</h3>
          <div className="space-y-4">
            {trends.map((item: any, i: number) => (
              <div key={i} className="flex items-center justify-between border-b border-slate-900 pb-3 last:border-b-0 last:pb-0">
                <div>
                  <span className="block text-sm font-semibold text-slate-200">{item.topic}</span>
                  <span className="block text-[10px] text-slate-500">Extracted {item.count} times</span>
                </div>
                <div className="flex items-center gap-1 text-emerald-400 text-xs font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full">
                  {item.growth}
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
export default Dashboard;
