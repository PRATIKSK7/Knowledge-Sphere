import React, { useEffect, useState, useRef } from 'react';
import { api } from '../services/api';
import { Document, IngestionStatus } from '../types';
import { 
  Upload, 
  File, 
  Trash2, 
  Loader2, 
  CheckCircle2, 
  XCircle,
  FileSpreadsheet,
  FileCode,
  FileText
} from 'lucide-react';

export const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents/');
      setDocuments(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Poll for processing document updates every 4 seconds
    const interval = setInterval(() => {
      fetchDocuments();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const uploadFile = async (file: File) => {
    // 1. Frontend validation: Size
    const MAX_MB = 50;
    if (file.size > MAX_MB * 1024 * 1024) {
      alert(`Upload failed: File exceeds ${MAX_MB} MB limit.`);
      return;
    }

    // 2. Frontend validation: Extension
    const allowedExtensions = ['pdf', 'docx', 'doc', 'txt', 'csv', 'html', 'htm'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !allowedExtensions.includes(ext)) {
      alert(`Upload failed: Unsupported file type: .${ext || 'unknown'}`);
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.postForm('/documents/upload', formData);
      fetchDocuments();
    } catch (err: any) {
      console.error("UPLOAD ERROR", err);
      console.log("RESPONSE", err.response);
      console.log("DATA", err.response?.data);
      
      let errorMsg = err.response?.data?.detail || err.message || 'Unsupported format or file size exceeded.';
      if (typeof errorMsg === 'object') {
        // e.g., FastAPI 422 validation errors return an array of objects
        errorMsg = JSON.stringify(errorMsg);
      }
      
      alert(`Upload failed: ${errorMsg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0]);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this document? All embedded vectors and concepts in the knowledge graph will be cleared.')) return;
    try {
      await api.delete(`/documents/${id}`);
      setDocuments(documents.filter((doc) => doc.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const renderStatus = (status: IngestionStatus) => {
    switch (status) {
      case 'completed':
        return (
          <span className="flex items-center gap-1.5 text-emerald-400 text-xs bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            <CheckCircle2 className="h-3.5 w-3.5" /> Ready
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center gap-1.5 text-rose-400 text-xs bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/20">
            <XCircle className="h-3.5 w-3.5" /> Failed
          </span>
        );
      case 'pending':
      case 'parsing':
      case 'chunking':
      case 'extracting':
      case 'indexing':
        return (
          <span className="flex items-center gap-1.5 text-blue-400 text-xs bg-blue-500/10 px-2.5 py-1 rounded-full border border-blue-500/20 animate-pulse">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> {status}
          </span>
        );
      default:
        return status;
    }
  };

  const getFileIcon = (mime: string) => {
    if (mime.includes('pdf')) return <File className="h-8 w-8 text-rose-500" />;
    if (mime.includes('csv')) return <FileSpreadsheet className="h-8 w-8 text-emerald-500" />;
    if (mime.includes('html')) return <FileCode className="h-8 w-8 text-amber-500" />;
    return <FileText className="h-8 w-8 text-blue-500" />;
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
          Document Library
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Upload and index research papers, reports, HTML notes, CSV tables, or DOCX scripts.
        </p>
      </div>

      {/* Drag & Drop Box */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`glass-panel border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 ${
          dragActive
            ? 'border-blue-500 bg-blue-500/5'
            : 'border-slate-800 hover:border-blue-500/40 hover:bg-slate-900/10'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          accept=".pdf,.docx,.doc,.txt,.csv,.html,.htm"
        />
        <div className="flex flex-col items-center gap-3">
          <div className="p-4 bg-slate-900 rounded-full border border-slate-800 text-slate-400 group-hover:scale-105 transition-transform">
            {uploading ? (
              <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
            ) : (
              <Upload className="h-8 w-8" />
            )}
          </div>
          <h3 className="font-bold text-slate-200">
            {uploading ? 'Processing Document...' : 'Drag & Drop files here'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm">
            Supported: PDF, DOCX, CSV, TXT, HTML (Max 50MB per file). We automatically extract metadata and map relationships.
          </p>
        </div>
      </div>

      {/* Documents Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-6 border-b border-slate-800/60">
          <h3 className="font-bold text-slate-200">Indexed Resources</h3>
        </div>

        {documents.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <File className="h-10 w-10 mx-auto mb-3 text-slate-700" />
            <p className="text-sm">No documents uploaded yet. Upload a document to build your knowledge graph.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-900">
            {documents.map((doc) => (
              <div key={doc.id} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-900/10 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="p-2 bg-slate-900 rounded-lg border border-slate-850">
                    {getFileIcon(doc.mime_type)}
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-200 text-sm">{doc.title}</h4>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {doc.filename} • {(doc.file_size / (1024 * 1024)).toFixed(2)} MB • Uploaded {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                    
                    {/* Authors and Keywords badges */}
                    {doc.authors && doc.authors.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        <span className="text-[10px] text-slate-500 font-semibold uppercase self-center mr-1">Authors:</span>
                        {doc.authors.slice(0, 3).map((author, idx) => (
                          <span key={idx} className="text-[10px] text-slate-350 bg-slate-800 px-2 py-0.5 rounded">
                            {author}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4 self-end md:self-center">
                  {renderStatus(doc.status)}
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all border border-transparent hover:border-rose-500/20"
                    title="Delete document"
                  >
                    <Trash2 className="h-4.5 w-4.5" />
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
export default Documents;
