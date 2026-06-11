import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Lightbulb, Loader2, Sparkles, HelpCircle, Compass } from 'lucide-react';

export const Gaps: React.FC = () => {
  const [gaps, setGaps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchGaps = async () => {
    setLoading(true);
    try {
      const res = await api.get('/graph/gaps');
      setGaps(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGaps();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center flex-col gap-3">
        <Loader2 className="h-8 w-8 text-amber-500 animate-spin" />
        <p className="text-slate-400 text-sm">Analyzing graph topological holes...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent flex items-center gap-3">
          <Lightbulb className="h-8 w-8 text-amber-500" />
          Research Gap Detector
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Identifies isolated nodes, structural holes, and weak relationships in your library graph.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {gaps.map((gap, idx) => (
          <div key={idx} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 hover:border-amber-500/20 transition-all group relative overflow-hidden">
            {/* Background design glow */}
            <div className="absolute -top-12 -right-12 w-24 h-24 bg-amber-500/5 rounded-full blur-xl group-hover:bg-amber-500/10 transition-colors" />

            <div className="flex items-start gap-4">
              <div className="p-3 bg-amber-500/10 rounded-xl text-amber-400">
                <Compass className="h-5 w-5 animate-pulse" />
              </div>
              <div className="space-y-1">
                <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider">Concept Node:</span>
                <h3 className="text-lg font-bold text-slate-200">{gap.concept}</h3>
              </div>
            </div>

            <div className="space-y-2 border-t border-slate-900 pt-3">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <HelpCircle className="h-4 w-4" />
                <span className="font-semibold text-slate-350">Detection Reason</span>
              </div>
              <p className="text-xs text-slate-400 italic">"{gap.reason}"</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold">
                <Sparkles className="h-4 w-4" />
                <span>Innovation Pathways & Suggestions</span>
              </div>
              <ul className="space-y-1.5">
                {gap.suggestions?.map((sug: string, idx2: number) => (
                  <li key={idx2} className="text-xs text-slate-300 pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-blue-500">
                    {sug}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
export default Gaps;
