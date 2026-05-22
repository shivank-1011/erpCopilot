import React, { useState, useCallback, useRef } from 'react';
import { api } from '../api.js';
import { FileText, CheckCircle, Blocks, UploadCloud, RefreshCw, Inbox, Trash2 } from 'lucide-react';

function formatBytes(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadPanel({ documents, setDocuments, onRefresh }) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleFiles = useCallback(
    async (files) => {
      const file = files[0];
      if (!file) return;

      const ext = file.name.split('.').pop().toLowerCase();
      if (!['pdf', 'docx'].includes(ext)) {
        setUploadMsg({ type: 'error', text: `Unsupported file type ".${ext}". Upload PDF or DOCX.` });
        return;
      }

      setUploading(true);
      setUploadMsg(null);

      try {
        const result = await api.upload(file);

        if (result.status === 'duplicate') {
          setUploadMsg({ type: 'warn', text: result.message });
        } else {
          setUploadMsg({
            type: 'success',
            text: `✅ "${file.name}" uploaded! Embedding ${result.document.chunk_count} chunks in background...`,
          });
          onRefresh(); // reload document list
        }
      } catch (err) {
        setUploadMsg({ type: 'error', text: `Upload failed: ${err.message}` });
      } finally {
        setUploading(false);
        // Clear message after 6 seconds
        setTimeout(() => setUploadMsg(null), 6000);
      }
    },
    [onRefresh]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Delete "${filename}"? This will remove all its chunks from the vector store.`)) return;
    try {
      await api.documents.delete(docId);
      onRefresh();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Stats row */}
      <div className="three-col">
        {[
          { label: 'Documents', value: documents.length, icon: <FileText size={24} /> },
          { label: 'Ready', value: documents.filter((d) => d.status === 'ready').length, icon: <CheckCircle size={24} /> },
          {
            label: 'Total Chunks',
            value: documents.reduce((s, d) => s + (d.chunk_count || 0), 0),
            icon: <Blocks size={24} />,
          },
        ].map((s) => (
          <div key={s.label} className="glass-card stat-card">
            <div style={{ fontSize: 24, marginBottom: 8 }}>{s.icon}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Upload zone */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div className="section-title">Upload Document</div>

        <div
          id="upload-dropzone"
          className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
          onClick={() => !uploading && fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          role="button"
          tabIndex={0}
          aria-label="Drop files here or click to upload"
          onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            style={{ display: 'none' }}
            onChange={(e) => handleFiles(e.target.files)}
            id="file-input"
          />

          {uploading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
              <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3, color: 'var(--violet)' }} />
              <span style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Uploading &amp; parsing...</span>
              <div className="progress-bar-wrap" style={{ width: 200 }}>
                <div className="progress-bar-fill" style={{ width: '100%' }} />
              </div>
            </div>
          ) : (
            <>
              <span className="upload-icon"><UploadCloud size={40} /></span>
              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                Drop your ERP document here
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Supports <span className="badge badge-red" style={{ marginRight: 4 }}>PDF</span>
                <span className="badge badge-blue">DOCX</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
                or click to browse — max 50 MB
              </div>
            </>
          )}
        </div>

        {/* Upload feedback */}
        {uploadMsg && (
          <div
            className={`alert alert-${
              uploadMsg.type === 'error' ? 'error' : uploadMsg.type === 'warn' ? 'warn' : 'success'
            }`}
            style={{ marginTop: 12 }}
          >
            {uploadMsg.text}
          </div>
        )}
      </div>

      {/* Document list */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div className="section-title" style={{ marginBottom: 0 }}>Uploaded Documents</div>
          <button className="btn btn-ghost btn-sm" onClick={onRefresh} id="btn-refresh-docs">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="empty-state" style={{ padding: '40px 0' }}>
            <span className="empty-icon"><Inbox size={48} /></span>
            <div className="empty-title">No documents yet</div>
            <div className="empty-desc">Upload your first ERP document to get started</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {documents.map((doc) => (
              <div key={doc.id} className="file-item">
                <div className={`file-icon ${doc.file_type}`}>
                  <FileText size={20} />
                </div>
                <div className="file-info">
                  <div className="file-name" title={doc.filename}>{doc.filename}</div>
                  <div className="file-meta">
                    {doc.chunk_count} chunks · {doc.page_count} pages · {formatBytes(doc.file_size_bytes)}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`status-dot ${doc.status}`} title={doc.status} />
                  <span
                    className={`badge badge-${
                      doc.status === 'ready' ? 'emerald' : doc.status === 'processing' ? 'amber' : 'red'
                    }`}
                  >
                    {doc.status}
                  </span>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    title="Delete document"
                    id={`btn-delete-doc-${doc.id}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
