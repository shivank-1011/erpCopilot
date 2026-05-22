/**
 * api.js — Centralized API service.
 * All fetch calls go through here so the base URL is defined once.
 * Vite proxies /api → http://localhost:8000 during development.
 */

const BASE = import.meta.env.VITE_API_URL || '/api';

async function request(method, path, body = null, isFile = false) {
  const opts = {
    method,
    headers: isFile ? {} : { 'Content-Type': 'application/json' },
    body: body
      ? isFile
        ? body
        : JSON.stringify(body)
      : undefined,
  };

  const res = await fetch(`${BASE}${path}`, opts);

  if (!res.ok) {
    let errMsg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      errMsg = data.detail || data.message || errMsg;
    } catch { /* ignore parse errors */ }
    throw new Error(errMsg);
  }

  return res.json();
}

// ── Documents ────────────────────────────────────────────────
export const api = {
  documents: {
    list: () => request('GET', '/documents'),

    get: (id) => request('GET', `/documents/${id}`),

    delete: (id) => request('DELETE', `/documents/${id}`),

    chunks: (id) => request('GET', `/documents/${id}/chunks`),
  },

  // ── Ingestion ────────────────────────────────────────────
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('POST', '/upload', formData, true);
  },

  // ── Chat / RAG ───────────────────────────────────────────
  chat: (question, docIds = null) =>
    request('POST', '/chat', {
      question,
      doc_ids: docIds,
    }),

  // ── Test Case Generation ─────────────────────────────────
  generateTests: (chunkText, source) =>
    request('POST', '/generate-tests', {
      chunk_text: chunkText,
      source,
    }),

  // ── Health ───────────────────────────────────────────────
  health: () => fetch('/health').then((r) => r.json()),
};
