import React from 'react';

export default function SourceViewer({ sources }) {
  if (!sources || sources.length === 0) {
    return (
      <div className="glass-card">
        <div className="empty-state">
          <span className="empty-icon">🔍</span>
          <div className="empty-title">No sources selected</div>
          <div className="empty-desc">
            Click a source citation in the Chat panel to view the exact document chunks
            that were retrieved to generate the answer.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div className="glass-card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 24 }}>🔍</span>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
              Retrieved Source Chunks
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              {sources.length} chunk{sources.length !== 1 ? 's' : ''} used to generate this answer
            </div>
          </div>
          <div style={{ marginLeft: 'auto' }}>
            <span className="badge badge-violet">{sources.length} sources</span>
          </div>
        </div>
      </div>

      {/* Source items */}
      <div className="source-viewer">
        {sources.map((src, idx) => (
          <div key={idx} className="source-item" id={`source-item-${idx}`}>
            {/* Source header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
              <span className="badge badge-violet">#{idx + 1}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', flex: 1, minWidth: 0 }}>
                {src.filename}
              </span>
              <span className="badge badge-grey">Page {src.page_num}</span>
              {src.chunk_id !== undefined && (
                <span className="badge badge-blue" style={{ fontFamily: 'monospace', fontSize: 10 }}>
                  chunk {src.chunk_id}
                </span>
              )}
            </div>

            {/* Source label */}
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, fontStyle: 'italic' }}>
              📍 {src.source}
            </div>

            {/* Chunk text */}
            <div className="source-text">{src.text}</div>
          </div>
        ))}
      </div>

      {/* Footer note */}
      <div className="alert alert-info" style={{ fontSize: 12 }}>
        💡 <strong>How retrieval works:</strong> Your question was embedded using Gemini's
        text-embedding-004 model, then compared against all stored chunk vectors using cosine
        similarity search (pgvector). These are the top-{sources.length} most semantically
        similar chunks to your question.
      </div>
    </div>
  );
}
