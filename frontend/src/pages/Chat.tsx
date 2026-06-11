import React, { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { ChatMessage } from '../types';
import { 
  Send, 
  Bot, 
  User as UserIcon, 
  BookOpen, 
  HelpCircle, 
  ExternalLink, 
  Award, 
  Network,
  FileDown
} from 'lucide-react';

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Hello! I am your AI Research Intelligence Assistant. Ask me complex multi-hop questions across your library documents, and I will search the vector space and traverse the knowledge graph to compile explainable answers.',
      timestamp: new Date().toLocaleTimeString(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Explainability drawer/details state
  const [activeExplainMessage, setActiveExplainMessage] = useState<ChatMessage | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      text: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const historyPayload = messages
        .filter(m => m.id !== 'welcome')
        .map(m => ({
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.text
        }));

      const res = await api.post('/search/chat', { 
        query: userMessage.text,
        history: historyPayload
      });
      
      const botMessage: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: 'bot',
        text: res.data.answer,
        timestamp: new Date().toLocaleTimeString(),
        citations: res.data.citations,
        confidenceScore: res.data.confidence_score,
        graphPaths: res.data.graph_paths,
      };

      setMessages((prev) => [...prev, botMessage]);
      
      // Auto-set the latest bot message for explainability view
      setActiveExplainMessage(botMessage);
    } catch (err: any) {
      console.error(err);
      let errorMsg = err.response?.data?.detail || 'Sorry, I encountered an error executing that query in the agent chain.';
      if (typeof errorMsg === 'object') {
        errorMsg = JSON.stringify(errorMsg);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'bot',
          text: `Backend Error: ${errorMsg}`,
          timestamp: new Date().toLocaleTimeString(),
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async (msg: ChatMessage) => {
    if (!msg) return;
    try {
      const response = await api.post('/graph/report/pdf', {
        query: messages.find(m => m.sender === 'user')?.text || 'Research Query',
        answer: msg.text,
        citations: msg.citations || [],
        confidence_score: msg.confidenceScore || 0.85
      }, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `research_report_${Date.now()}.pdf`;
      link.click();
    } catch (err) {
      console.error('PDF generation error', err);
      alert('Failed to generate PDF report.');
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[80vh]">
      {/* Chat sandbox area */}
      <div className="lg:col-span-2 flex flex-col h-full glass-panel border border-slate-850 rounded-2xl overflow-hidden relative">
        <div className="p-4 border-b border-slate-900 bg-slate-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-blue-500" />
            <h3 className="font-bold text-slate-200 text-sm">Research Chat Agent</h3>
          </div>
          {loading && <span className="text-[10px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full animate-pulse">Agent reasoning...</span>}
        </div>

        {/* Messages space */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-[85%] ${
                msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''
              }`}
            >
              <div className={`h-8 w-8 rounded-lg shrink-0 flex items-center justify-center border ${
                msg.sender === 'user'
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-slate-900 border-slate-800 text-blue-400'
              }`}>
                {msg.sender === 'user' ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              <div className="space-y-2">
                <div className={`p-4 rounded-2xl text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-blue-600/15 border border-blue-500/30 text-slate-100'
                    : 'bg-slate-900/60 border border-slate-850 text-slate-200'
                }`}>
                  <p>{msg.text}</p>
                </div>
                
                {/* Meta actions bar */}
                {msg.sender === 'bot' && msg.id !== 'welcome' && (
                  <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-400">
                    <span>{msg.timestamp}</span>
                    <button
                      onClick={() => setActiveExplainMessage(msg)}
                      className="hover:text-blue-400 font-semibold transition-colors flex items-center gap-1"
                    >
                      <HelpCircle className="h-3 w-3" /> Explainable AI Panel
                    </button>
                    <button
                      onClick={() => handleExportPDF(msg)}
                      className="hover:text-emerald-400 font-semibold transition-colors flex items-center gap-1"
                    >
                      <FileDown className="h-3 w-3" /> Export PDF
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 max-w-[80%]">
              <div className="h-8 w-8 rounded-lg shrink-0 bg-slate-900 border border-slate-800 text-blue-400 flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <div className="bg-slate-900/30 border border-slate-850 p-4 rounded-2xl flex items-center gap-2">
                <span className="h-2 w-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="h-2 w-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="h-2 w-2 bg-blue-500 rounded-full animate-bounce" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input box */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-slate-900 flex gap-2">
          <input
            type="text"
            required
            disabled={loading}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me a research question..."
            className="flex-1 px-4 py-3 rounded-lg glass-input text-xs"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-all flex items-center justify-center shrink-0 disabled:opacity-55"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>

      {/* Explainable AI Sidebar Panels (Module 17) */}
      <div className="glass-panel border border-slate-850 rounded-2xl p-5 h-full flex flex-col overflow-y-auto space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-900">
          <Award className="h-5 w-5 text-indigo-400" />
          <h3 className="font-bold text-slate-200 text-sm">Explainable AI Details</h3>
        </div>

        {activeExplainMessage ? (
          <div className="space-y-6 flex-1">
            {/* Confidence metric */}
            <div className="space-y-1 bg-slate-900/50 p-3 rounded-xl border border-slate-850">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-semibold">Confidence Metric</span>
                <span className="text-blue-400 font-bold">{(activeExplainMessage.confidenceScore || 0.85) * 100}%</span>
              </div>
              <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full"
                  style={{ width: `${(activeExplainMessage.confidenceScore || 0.85) * 100}%` }}
                />
              </div>
            </div>

            {/* Traversed paths (Module 10 / 17) */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold">
                <Network className="h-4 w-4" />
                <span>Traversed Graph Paths</span>
              </div>
              {activeExplainMessage.graphPaths && activeExplainMessage.graphPaths.length > 0 ? (
                <div className="space-y-2">
                  {activeExplainMessage.graphPaths.map((p: any, idx: number) => (
                    <div key={idx} className="bg-slate-900/30 p-2.5 rounded-xl border border-slate-850 text-[10px] text-slate-350">
                      {p.path_sequence?.join(" → ")}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-slate-500 italic">No explicit semantic paths traversed. Relied purely on vector retrieval space.</p>
              )}
            </div>

            {/* Citations used */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-blue-400 font-semibold">
                <BookOpen className="h-4 w-4" />
                <span>Retrieved Context Sources</span>
              </div>
              {activeExplainMessage.citations && activeExplainMessage.citations.length > 0 ? (
                <div className="space-y-2.5 max-h-[40vh] overflow-y-auto pr-1">
                  {activeExplainMessage.citations.map((c: any, idx: number) => (
                    <div key={idx} className="bg-slate-900/30 p-3 rounded-xl border border-slate-850 space-y-1">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="text-blue-400 font-bold">{c.citation_key}</span>
                        <span className="text-slate-500 truncate max-w-[150px]">{c.document_title}</span>
                      </div>
                      <p className="text-[10px] text-slate-350 italic">"{c.text_snippet}"</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-slate-500 italic">No reference markers found.</p>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-slate-500 p-4">
            <HelpCircle className="h-8 w-8 mb-2 text-slate-700" />
            <p className="text-xs">Ask a question to see confidence metrics, source document alignments, and Neo4j paths traversed by the agent graph.</p>
          </div>
        )}
      </div>
    </div>
  );
};
export default Chat;
