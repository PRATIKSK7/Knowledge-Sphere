import React, { useState } from 'react';
import { api } from '../services/api';
import { BookOpen, RefreshCw, FileText, Download } from 'lucide-react';

export const LitReview: React.FC = () => {
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState('APA');
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setLoading(true);
    setReview('');

    try {
      const res = await api.post('/graph/literature-review', {
        topic,
        format: style
      });
      setReview(res.data.review);
    } catch (err: any) {
      console.error(err);
      let errorMsg = err.response?.data?.detail || 'Error compiling literature review.';
      if (typeof errorMsg === 'object') {
        errorMsg = JSON.stringify(errorMsg);
      }
      alert(`Synthesis Failed: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([review], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = `Literature_Review_${topic.replace(/\s+/g, "_")}.md`;
    document.body.appendChild(element);
    element.click();
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent flex items-center gap-3">
          <BookOpen className="h-8 w-8 text-blue-500" />
          Literature Review Compiler
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Synthesize references in your library. Automatically compile APA/IEEE format reviews.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Topic Input Box */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4 h-fit">
          <h3 className="text-sm font-bold text-slate-200">Compile Setup</h3>
          
          <form onSubmit={handleGenerate} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide">Research Topic / Keywords</label>
              <input
                type="text"
                required
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Attention Mechanism in Transformer nets"
                className="w-full px-3 py-2 rounded-lg glass-input text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide">Citation Standard Style</label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="w-full px-3 py-2 rounded-lg glass-input text-xs"
              >
                <option value="APA">APA 7th Edition</option>
                <option value="IEEE">IEEE Reference Style</option>
                <option value="MLA">MLA Format</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold py-2.5 rounded-lg transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" /> Compiling sources...
                </>
              ) : (
                'Generate Review'
              )}
            </button>
          </form>
        </div>

        {/* Lit Review Compile Output */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800 min-h-[50vh] flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center pb-4 border-b border-slate-900 mb-4">
              <span className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-400" /> Compiled Synthesis Output
              </span>
              {review && (
                <button
                  onClick={handleDownload}
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 bg-slate-900 px-3 py-1.5 rounded border border-slate-800 hover:bg-slate-800"
                >
                  <Download className="h-3.5 w-3.5" /> Download Markdown
                </button>
              )}
            </div>

            {review ? (
              <div className="prose prose-invert max-w-none text-xs text-slate-300 leading-relaxed whitespace-pre-wrap space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                {review}
              </div>
            ) : (
              <div className="text-center text-slate-500 py-24">
                <FileText className="h-10 w-10 mx-auto mb-3 text-slate-700 animate-pulse" />
                <p className="text-sm">Set your topic parameters and compile references to generate a review.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
export default LitReview;
