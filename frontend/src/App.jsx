import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar.jsx';
import UploadPanel from './components/UploadPanel.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import TestCasePanel from './components/TestCasePanel.jsx';
import SourceViewer from './components/SourceViewer.jsx';
import { api } from './api.js';

const PAGE_CONFIG = {
  upload: {
    title: 'Document Library',
    subtitle: 'Upload and manage your ERP documents — PDF and DOCX supported',
    icon: '📁',
  },
  chat: {
    title: 'ERP Assistant',
    subtitle: 'Ask questions about your documents — answers are grounded in your content with citations',
    icon: '💬',
  },
  testgen: {
    title: 'Test Case Generator',
    subtitle: 'Select a document section and generate structured QA test cases with Gemini AI',
    icon: '🧪',
  },
  sources: {
    title: 'Source Viewer',
    subtitle: 'Inspect the exact document chunks retrieved to generate each answer',
    icon: '🔍',
  },
};

export default function App() {
  const [activePanel, setActivePanel] = useState('upload');
  const [documents, setDocuments]     = useState([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [activeSources, setActiveSources] = useState([]);

  // Load documents on mount
  const loadDocuments = useCallback(async () => {
    setDocsLoading(true);
    try {
      const data = await api.documents.list();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setDocsLoading(false);
    }
  }, []);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  // Auto-refresh every 5 seconds while any doc is processing
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === 'processing');
    if (!hasProcessing) return;
    const interval = setInterval(loadDocuments, 5000);
    return () => clearInterval(interval);
  }, [documents, loadDocuments]);

  // When source chip is clicked in chat, switch to sources panel
  const handleSetActiveSource = (sources) => {
    setActiveSources(sources);
    setActivePanel('sources');
  };

  const page = PAGE_CONFIG[activePanel];

  return (
    <div className="app-layout">
      <Sidebar activePanel={activePanel} setActivePanel={setActivePanel} />

      <main className="main-content">
        {/* Page Header */}
        <header className="page-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 26 }}>{page.icon}</span>
            <div>
              <h1 className="page-title">{page.title}</h1>
              <p className="page-subtitle">{page.subtitle}</p>
            </div>
            {/* Doc count badge in header */}
            {documents.length > 0 && (
              <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className="badge badge-violet">
                  {documents.length} doc{documents.length !== 1 ? 's' : ''}
                </span>
                {documents.some((d) => d.status === 'processing') && (
                  <span className="badge badge-amber">
                    <span className="status-dot processing" />
                    Processing...
                  </span>
                )}
              </div>
            )}
          </div>
        </header>

        {/* Panel Content */}
        <div className="panel-container">
          <div style={{ display: activePanel === 'upload' ? 'block' : 'none' }}>
            <UploadPanel
              documents={documents}
              setDocuments={setDocuments}
              onRefresh={loadDocuments}
            />
          </div>

          <div style={{ display: activePanel === 'chat' ? 'block' : 'none' }}>
            <ChatPanel
              documents={documents}
              setActiveSource={handleSetActiveSource}
            />
          </div>

          <div style={{ display: activePanel === 'testgen' ? 'block' : 'none' }}>
            <TestCasePanel documents={documents} />
          </div>

          <div style={{ display: activePanel === 'sources' ? 'block' : 'none' }}>
            <SourceViewer sources={activeSources} />
          </div>
        </div>
      </main>
    </div>
  );
}
