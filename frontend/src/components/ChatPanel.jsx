import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../api.js';

function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="message-avatar">🤖</div>
      <div className="message-bubble" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{
                width: 6, height: 6,
                borderRadius: '50%',
                background: 'var(--emerald)',
                animation: `pulse 1.2s ${i * 0.2}s infinite`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ChatPanel({ documents, setActiveSource }) {
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [filterDocId, setFilterDocId] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const readyDocs = documents.filter((d) => d.status === 'ready');

  const sendMessage = async () => {
    const question = input.trim();
    if (!question || loading) return;

    if (readyDocs.length === 0) {
      setError('Please upload and process at least one document first.');
      return;
    }

    // Add user message
    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const docIds = filterDocId ? [filterDocId] : null;
      const result = await api.chat(question, docIds);

      setMessages((prev) => [
        ...prev,
        {
          role:    'assistant',
          content: result.answer,
          sources: result.sources,
        },
      ]);
    } catch (err) {
      setError(`Error: ${err.message}`);
      setMessages((prev) => [
        ...prev,
        {
          role:    'assistant',
          content: '⚠️ I encountered an error processing your question. Please try again.',
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    if (messages.length > 0 && window.confirm('Clear chat history?')) {
      setMessages([]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 130px)' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        {/* Document scope selector */}
        <select
          id="chat-doc-filter"
          className="input-field"
          style={{ maxWidth: 280, padding: '8px 12px' }}
          value={filterDocId ?? ''}
          onChange={(e) => setFilterDocId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">🌐 Search all documents</option>
          {readyDocs.map((d) => (
            <option key={d.id} value={d.id}>
              {d.file_type === 'pdf' ? '📕' : '📘'} {d.filename}
            </option>
          ))}
        </select>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          {messages.length > 0 && (
            <button className="btn btn-ghost btn-sm" onClick={clearChat} id="btn-clear-chat">
              🗑 Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="empty-state" style={{ flex: 1 }}>
              <span className="empty-icon">💬</span>
              <div className="empty-title">Ask a question</div>
              <div className="empty-desc">
                Ask anything about your uploaded ERP documents.
                I'll find the relevant sections and give you a grounded answer with citations.
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8, justifyContent: 'center' }}>
                {[
                  'What changed in v2.3 GL posting?',
                  'Explain the three-way invoice matching rules',
                  'What are the approval thresholds?',
                  'What is error code FI-102?',
                ].map((q) => (
                  <button
                    key={q}
                    className="source-chip"
                    onClick={() => { setInput(q); textareaRef.current?.focus(); }}
                    style={{ fontSize: 12, cursor: 'pointer' }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div>
                <div className="message-bubble">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="message-sources">
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', alignSelf: 'center' }}>Sources:</span>
                    {msg.sources.map((src, i) => (
                      <button
                        key={i}
                        className="source-chip"
                        onClick={() => setActiveSource(msg.sources)}
                        id={`source-chip-${idx}-${i}`}
                        title={src.text}
                      >
                        📄 {src.filename} p.{src.page_num}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && <TypingIndicator />}

          {error && (
            <div className="alert alert-error" style={{ margin: '0 20px' }}>
              ⚠️ {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <textarea
            ref={textareaRef}
            id="chat-input"
            className="input-field"
            placeholder="Ask about your ERP documents... (Shift+Enter for new line)"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              // Auto-resize
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
            onKeyDown={handleKeyDown}
            disabled={loading}
            rows={1}
          />
          <button
            id="btn-send-chat"
            className="btn btn-primary"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{ height: 44, flexShrink: 0 }}
          >
            {loading ? <span className="spinner" style={{ color: 'white' }} /> : '↑'}
          </button>
        </div>
      </div>
    </div>
  );
}
