import React, { useState, useEffect } from 'react';
import { api } from '../api.js';

function TestCaseCard({ tc, type }) {
  const [expanded, setExpanded] = useState(false);
  const typeConfig = {
    positive: { label: 'Positive', badge: 'badge-emerald', class: 'positive', icon: '✅' },
    negative: { label: 'Negative', badge: 'badge-red',     class: 'negative', icon: '❌' },
    edge:     { label: 'Edge Case', badge: 'badge-amber',  class: 'edge',     icon: '⚠️' },
  }[type];

  return (
    <div className={`test-case-card ${typeConfig.class}`}>
      <div className="test-case-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
          <span>{typeConfig.icon}</span>
          <span className="test-case-title">{tc.title}</span>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
          <span className={`badge ${typeConfig.badge}`}>{typeConfig.label}</span>
          <span className="test-case-id">{tc.test_id}</span>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setExpanded(!expanded)}
            style={{ padding: '4px 8px', fontSize: 11 }}
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {expanded && (
        <>
          {tc.preconditions && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>
                Preconditions
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>{tc.preconditions}</div>
            </div>
          )}

          {tc.test_steps && tc.test_steps.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>
                Test Steps
              </div>
              <ul className="test-steps">
                {tc.test_steps.map((step, i) => (
                  <li key={i} className="test-step">
                    <span className="step-num">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {tc.test_data && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>
                Test Data
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono, monospace)' }}>
                {tc.test_data}
              </div>
            </div>
          )}

          <div className="expected-result">
            <strong>Expected Result</strong>
            {tc.expected_result}
          </div>
        </>
      )}
    </div>
  );
}

export default function TestCasePanel({ documents }) {
  const [selectedDocId, setSelectedDocId]   = useState('');
  const [chunks, setChunks]                 = useState([]);
  const [chunksLoading, setChunksLoading]   = useState(false);
  const [selectedChunk, setSelectedChunk]   = useState(null);
  const [generating, setGenerating]         = useState(false);
  const [testResult, setTestResult]         = useState(null);
  const [error, setError]                   = useState(null);
  const [activeTab, setActiveTab]           = useState('positive');

  const readyDocs = documents.filter((d) => d.status === 'ready');

  // Load chunks when document selected
  useEffect(() => {
    if (!selectedDocId) { setChunks([]); return; }

    setChunksLoading(true);
    setSelectedChunk(null);
    setTestResult(null);

    api.documents.chunks(selectedDocId)
      .then((data) => setChunks(data.chunks || []))
      .catch((err) => setError(`Failed to load chunks: ${err.message}`))
      .finally(() => setChunksLoading(false));
  }, [selectedDocId]);

  const handleGenerate = async () => {
    if (!selectedChunk) return;
    setGenerating(true);
    setTestResult(null);
    setError(null);

    try {
      const result = await api.generateTests(selectedChunk.text, selectedChunk.source);
      setTestResult(result);
      setActiveTab('positive');
    } catch (err) {
      setError(`Generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const allTests = testResult
    ? [
        ...testResult.positive_tests.map((t) => ({ ...t, _type: 'positive' })),
        ...testResult.negative_tests.map((t) => ({ ...t, _type: 'negative' })),
        ...testResult.edge_cases.map((t) => ({ ...t, _type: 'edge' })),
      ]
    : [];

  const downloadJSON = () => {
    if (!testResult) return;
    const blob = new Blob([JSON.stringify(testResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_cases_${testResult.feature_name.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', gap: 20, height: 'calc(100vh - 130px)' }}>
      {/* Left: Chunk selector */}
      <div style={{ width: 340, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="glass-card" style={{ padding: 20, flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className="section-title">Select Document Section</div>

          {/* Doc picker */}
          <select
            id="testgen-doc-select"
            className="input-field"
            style={{ marginBottom: 16 }}
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
          >
            <option value="">Choose a document...</option>
            {readyDocs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.file_type === 'pdf' ? '📕' : '📘'} {d.filename}
              </option>
            ))}
          </select>

          {/* Chunk list */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {chunksLoading && (
              <>
                {[1, 2, 3].map((i) => (
                  <div key={i} className="skeleton" style={{ height: 64 }} />
                ))}
              </>
            )}

            {!chunksLoading && chunks.length === 0 && selectedDocId && (
              <div className="empty-state" style={{ padding: '24px 0' }}>
                <span className="empty-icon" style={{ fontSize: 32 }}>⏳</span>
                <div className="empty-title" style={{ fontSize: 13 }}>No chunks available yet</div>
                <div className="empty-desc" style={{ fontSize: 12 }}>Document may still be processing</div>
              </div>
            )}

            {!chunksLoading && !selectedDocId && (
              <div className="empty-state" style={{ padding: '24px 0' }}>
                <span className="empty-icon" style={{ fontSize: 32 }}>👆</span>
                <div className="empty-title" style={{ fontSize: 13 }}>Select a document</div>
                <div className="empty-desc" style={{ fontSize: 12 }}>Choose a document above to see its sections</div>
              </div>
            )}

            {chunks.map((chunk, idx) => (
              <div
                key={chunk.uuid || idx}
                className={`chunk-item ${selectedChunk?.uuid === chunk.uuid ? 'selected' : ''}`}
                onClick={() => setSelectedChunk(chunk)}
                id={`chunk-item-${idx}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span className="badge badge-grey">p.{chunk.page_num}</span>
                  <span className="badge badge-violet">chunk {Number(chunk.chunk_index) + 1}</span>
                </div>
                <div className="chunk-preview">{chunk.preview}</div>
              </div>
            ))}
          </div>

          {/* Generate button */}
          <div style={{ marginTop: 16 }}>
            <button
              id="btn-generate-tests"
              className="btn btn-emerald"
              onClick={handleGenerate}
              disabled={!selectedChunk || generating}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {generating ? (
                <><span className="spinner" /> Generating...</>
              ) : (
                <>🧪 Generate Test Cases</>
              )}
            </button>
            {selectedChunk && (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, textAlign: 'center' }}>
                Selected: {selectedChunk.source}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right: Test case output */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {error && <div className="alert alert-error">⚠️ {error}</div>}

        {!testResult && !generating && (
          <div className="glass-card">
            <div className="empty-state">
              <span className="empty-icon">🧪</span>
              <div className="empty-title">No test cases yet</div>
              <div className="empty-desc">
                Select a document, pick a section, and click "Generate Test Cases"
                to create structured QA scenarios with Gemini AI
              </div>
            </div>
          </div>
        )}

        {generating && (
          <div className="glass-card" style={{ padding: 32 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
              <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3, color: 'var(--emerald)' }} />
              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Generating test cases...</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Gemini is analysing the document section and creating positive, negative, and edge case scenarios
              </div>
              <div className="progress-bar-wrap" style={{ width: 300 }}>
                <div className="progress-bar-fill" style={{ width: '100%' }} />
              </div>
            </div>
          </div>
        )}

        {testResult && (
          <>
            {/* Header */}
            <div className="glass-card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                    {testResult.feature_name}
                  </div>
                  {testResult.feature_summary && (
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{testResult.feature_summary}</div>
                  )}
                  <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <span className="badge badge-emerald">✅ {testResult.positive_tests.length} Positive</span>
                    <span className="badge badge-red">❌ {testResult.negative_tests.length} Negative</span>
                    <span className="badge badge-amber">⚠️ {testResult.edge_cases.length} Edge Cases</span>
                    <span className="badge badge-violet">Total: {testResult.total_tests}</span>
                  </div>
                </div>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={downloadJSON}
                  id="btn-download-tests"
                  title="Download as JSON"
                >
                  ⬇ Export JSON
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="tabs">
              {[
                { id: 'positive', label: '✅ Positive', count: testResult.positive_tests.length },
                { id: 'negative', label: '❌ Negative', count: testResult.negative_tests.length },
                { id: 'edge',     label: '⚠️ Edge Cases', count: testResult.edge_cases.length },
                { id: 'all',      label: '📋 All',        count: testResult.total_tests },
              ].map((tab) => (
                <button
                  key={tab.id}
                  className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                  id={`tab-${tab.id}`}
                >
                  {tab.label}
                  <span className="badge badge-grey" style={{ fontSize: 10 }}>{tab.count}</span>
                </button>
              ))}
            </div>

            {/* Test cards */}
            <div>
              {(activeTab === 'all' ? allTests : [
                ...(activeTab === 'positive' ? testResult.positive_tests.map((t) => ({ ...t, _type: 'positive' })) : []),
                ...(activeTab === 'negative' ? testResult.negative_tests.map((t) => ({ ...t, _type: 'negative' })) : []),
                ...(activeTab === 'edge'     ? testResult.edge_cases.map((t)     => ({ ...t, _type: 'edge' }))     : []),
              ]).map((tc, i) => (
                <TestCaseCard key={tc.test_id || i} tc={tc} type={tc._type} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
