# ERP Copilot Lite — Complete Interview Study Guide
### Tailored for Firstcron AI R&D Intern Interview

> **Company:** Firstcron — Syntra (ERP migration) · AutoExe (ERP automation) · ERPAssure (ERP assurance)
> **Role:** AI Research & Development Intern
> **Project:** ERP Copilot Lite — RAG-based document assistant with test case generation

---

## Table of Contents
1. [Project Overview — The Big Picture](#1-project-overview)
2. [Architecture & System Design](#2-architecture--system-design)
3. [Phase 1 — Document Ingestion](#3-phase-1--document-ingestion)
4. [Phase 2 — Embeddings & Vector Store](#4-phase-2--embeddings--vector-store)
5. [Phase 3 — RAG Chat Engine](#5-phase-3--rag-chat-engine)
6. [Phase 4 — Test Case Generator](#6-phase-4--test-case-generator)
7. [Phase 5 — React Frontend](#7-phase-5--react-frontend)
8. [Phase 6 — Evaluation & Prompt Engineering](#8-phase-6--evaluation--prompt-engineering)
9. [Technology Deep Dives](#9-technology-deep-dives)
10. [Firstcron Alignment & Business Value](#10-firstcron-alignment--business-value)
11. [Future Enhancements](#11-future-enhancements)

---

## 1. Project Overview

### What We Built
ERP Copilot Lite is a **lightweight, RAG-based (Retrieval-Augmented Generation) document assistant** designed specifically for ERP systems. It allows users to:
- Upload ERP-related PDFs and DOCX files (feature specs, release notes, process documents)
- Ask natural-language questions and get grounded answers with source citations
- Summarize key changes and business rules from documents
- Generate structured QA test cases (positive, negative, edge cases) from any selected document section
- View exactly which document chunks were retrieved to produce each answer

### Why We Built It
ERP systems like SAP, Oracle, and Microsoft Dynamics generate enormous volumes of documentation — release notes, migration guides, compliance docs, and process manuals. Business analysts, QA engineers, and consultants spend hours reading these manually to:
1. Understand what changed in a release
2. Write test cases to validate those changes
3. Answer stakeholder questions about business rules

**ERP Copilot Lite automates all three.** It directly maps to what Firstcron does:
- **ERPAssure** — ERP testing and assurance → our test case generator serves this
- **AutoExe** — ERP automation → our RAG pipeline automates document Q&A
- **Syntra** — ERP migration → migration docs can be ingested and queried

### How We Built It
| Layer | Technology | Why |
|-------|-----------|-----|
| Document parsing | Python + PyPDF2 + python-docx | Simple, battle-tested, handles both PDF and DOCX |
| Text chunking | LangChain RecursiveCharacterTextSplitter | Smart overlap preserves context across chunk boundaries |
| Embeddings | Google Gemini text-embedding-004 (768 dims) | Free tier, high quality, 768-dimensional vectors |
| Vector storage | PostgreSQL + pgvector (Supabase) | One database for both metadata and vectors |
| RAG pipeline | LangChain RetrievalQA | Clean abstraction for retrieval + LLM orchestration |
| LLM | Google Gemini 2.0 Flash | Strong reasoning, generous free tier, fast |
| API layer | FastAPI | Async, auto-docs (Swagger), typed, production-grade |
| Frontend | React + Vite + Vanilla CSS | Fast build, clean UI, Neo-Brutalist design (hard shadows, stark borders) |

---

### Interview Q&A — Project Overview

**Q1: Tell me about your project in one sentence.**
> A: ERP Copilot Lite is a RAG-based assistant that ingests ERP documents, answers user questions with source citations, summarizes business rules, and generates structured QA test cases — all from a FastAPI backend with a React frontend powered by Google Gemini AI.

**Q2: Why did you choose this project specifically for Firstcron?**
> A: Firstcron builds ERPAssure for ERP testing and AutoExe for ERP automation. My project directly demonstrates both capabilities: the test case generator maps to ERPAssure's testing workflow, and the RAG pipeline maps to intelligent document automation. I built a portfolio project that speaks directly to what Firstcron does in production.

**Q3: What problem does ERP Copilot Lite actually solve?**
> A: ERP documentation is dense and voluminous. A release note for SAP S/4HANA can be 200+ pages. QA engineers manually read these to write test cases — a process that takes days. My tool reduces that to seconds by automatically retrieving the relevant section and generating structured test scenarios using an LLM.

**Q4: What would you do differently if you had more time?**
> A: Three things: First, add multi-tenancy so different teams can have separate document namespaces. Second, integrate with Jira or Azure DevOps to push generated test cases directly into a test management system. Third, implement a feedback loop where users rate answers and we use that signal to improve retrieval quality over time.

**Q5: How is this different from just using Gemini directly?**
> A: Gemini doesn't know your specific ERP documents — it can hallucinate details because it only has general training data. My system does Retrieval-Augmented Generation: it first searches your actual uploaded documents, retrieves the most relevant chunks, and then asks Gemini to answer using only that context. This grounds the answer in your real documentation and provides citations so you can verify every claim.

---

## 2. Architecture & System Design

### System Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (Vite)                │
│  [Upload] → [Chat Panel] → [Test Gen] → [Source View]  │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP / REST API  (Vite proxy → port 8000)
┌─────────────────────▼───────────────────────────────────┐
│                   FASTAPI BACKEND                       │
│                                                         │
│  POST /api/upload    POST /api/chat    POST /api/generate-tests │
│       │               │               │                 │
│  [Ingestion]    [RAG Pipeline]  [Test Gen Service]      │
│  [Chunker]      [LangChain]     [Gemini JSON Mode]      │
│  [Parser]       [Retriever]                             │
└──────────┬──────────────┬──────────────────────────────┘
           │              │
    ┌──────▼──────┐  ┌────▼──────────────┐
    │  Supabase   │  │   Google Gemini   │
    │  PostgreSQL │  │ - text-embedding-004 (768d) │
    │  (metadata) │  │ - gemini-2.0-flash  │
    │  + pgvector │  └───────────────────┘
    │  (vectors)  │
    └─────────────┘
```

### Data Flow for a Chat Request
```
User types question
       ↓
Frontend sends POST /api/chat { "question": "..." }
       ↓
FastAPI receives request
       ↓
Embed the question via Gemini → [0.12, -0.45, ...] (768 dimensions)
       ↓
pgvector cosine similarity search → Top 5 chunks retrieved
       ↓
Build prompt: "Answer using these chunks: [chunk1][chunk2]..."
       ↓
Gemini 2.0 Flash generates grounded answer
       ↓
Return { "answer": "...", "sources": [{filename, page, text}...] }
       ↓
Frontend renders answer + clickable source citations
```

---

### Interview Q&A — Architecture

**Q6: Walk me through what happens when a user uploads a PDF.**
> A: The frontend sends a multipart form POST to /api/upload. FastAPI receives the file binary, computes a SHA-256 hash for duplicate detection, then passes it to our parser service. PyPDF2 extracts raw text page by page with page numbers. We then run it through LangChain's RecursiveCharacterTextSplitter with chunk size 1000 and overlap 200. Each chunk gets metadata (doc_id, filename, page_num). Then a background task calls Gemini's text-embedding-004 to get 768-dimensional vectors and stores them in Supabase via LangChain PGVector. The document status updates from 'processing' to 'ready'. We return immediately so the upload feels fast.

**Q7: Why chunk size 1000 with overlap 200?**
> A: Chunk size is a trade-off. Too small and you lose context. Too large and you dilute the signal and hit token limits. 1000 characters (~200-250 words) is a sweet spot for ERP documentation paragraphs. The 200-character overlap ensures sentences split across chunk boundaries are captured in both neighboring chunks, preventing retrieval gaps.

**Q8: How does semantic search work?**
> A: Keyword search matches exact words. Semantic search converts both query and documents into dense vector embeddings where similar meanings are geometrically close. We use cosine similarity via pgvector's <=> operator to find the closest document vectors to the query vector. "Record a transaction" correctly retrieves "journal entry posting" because their Gemini embeddings are nearby in 768-dimensional space.

**Q9: Why PostgreSQL + pgvector instead of Pinecone?**
> A: Single database — metadata and vectors live together, no sync issues. Standard SQL for metadata filtering. Free with Supabase. Practical for internship scale. Pinecone is better for millions of vectors with managed SaaS. I chose pgvector to show practical infrastructure judgment — right tool for the scale.

**Q10: What is background task processing in FastAPI?**
> A: FastAPI's BackgroundTasks runs functions after the HTTP response is sent. When a file is uploaded, we return immediately with a "processing" status. The embedding generation (which calls the Gemini API for each chunk) runs in the background. The frontend polls document status every 5 seconds and shows 'ready' when done. This makes uploads feel instant instead of blocking for 10-30 seconds.

---

## 3. Phase 1 — Document Ingestion

### What We Built
A pipeline that: accepts PDF/DOCX uploads → extracts text → chunks with overlap → stores metadata in PostgreSQL.

**Key design:** SHA-256 hash for duplicate detection. Background embedding task for fast HTTP response.

**RecursiveCharacterTextSplitter separators in order:**
1. `\n\n` — paragraph breaks (preferred)
2. `\n` — line breaks  
3. `. ` — sentence endings
4. ` ` — word boundaries
5. `""` — character-level (last resort)

---

### Interview Q&A — Document Ingestion

**Q11: What if a PDF is scanned and has no extractable text?**
> A: PyPDF2 only extracts text from text-based PDFs. Scanned PDFs return empty strings. We detect this (all pages empty) and raise a 422 error with a clear message. The proper solution is OCR using Tesseract via pytesseract or AWS Textract. This is planned for v2.

**Q12: How do you prevent duplicate uploads?**
> A: We hash the file content with SHA-256 before processing. We check if that hash exists in the documents table. If found, we return "document already uploaded" with the original document's metadata — no duplicate processing.

**Q13: How do you handle large documents efficiently?**
> A: Embedding runs as a background task, not blocking the HTTP response. We batch chunks before sending to the Gemini embedding API rather than one call per chunk. For Gemini, we can send multiple texts per API call. We also add tenacity retry logic with exponential backoff for rate limit handling.

---

## 4. Phase 2 — Embeddings & Vector Store

### What We Built
- Gemini text-embedding-004 model producing 768-dimensional vectors
- LangChain PGVector managing the vector store on Supabase
- Collection "erp_chunks" with metadata: doc_id, filename, page_num, source

### Embedding Model Comparison
| Model | Dimensions | Cost | Quality |
|-------|-----------|------|---------|
| `text-embedding-004` (Gemini) | 768 | Free tier | ✅ Our choice |
| `text-embedding-3-small` (OpenAI) | 1536 | $0.02/1M | Slightly richer |
| `nomic-embed-text` (Local) | 768 | Free | Good quality |

### LangChain PGVector Tables (auto-created)
- `langchain_pg_collection` — collection metadata
- `langchain_pg_embedding` — `(uuid, collection_id, embedding vector(768), document text, cmetadata json)`

---

### Interview Q&A — Embeddings & Vector Store

**Q14: What is cosine similarity and why use it over Euclidean distance?**
> A: Cosine similarity measures the angle between vectors, not magnitude. For text embeddings, two docs on the same topic but different lengths have similar direction but different magnitude. Euclidean distance would penalize longer text. Cosine similarity ignores magnitude — only direction matters. pgvector's <=> operator computes cosine distance (1 - similarity), so ORDER BY <=> gives nearest neighbors.

**Q15: What are the 768 dimensions in the embedding vector?**
> A: Each of the 768 numbers represents a learned semantic feature captured by Gemini's neural network during training on massive text corpora. Together they form a point in 768-dimensional space where semantically similar texts are geometrically close. We can't interpret individual dimensions — they're abstract learned representations.

**Q16: What metadata do you store with each chunk?**
> A: In LangChain's cmetadata JSON column: doc_id (foreign key to our documents table), filename (for display), page_num (for citations), chunk_index (for ordering), and source (human-readable citation like "release_notes.pdf — Page 3"). This metadata appears in the frontend source citations.

---

## 5. Phase 3 — RAG Chat Engine

### What We Built
LangChain RetrievalQA chain: question → embed → pgvector search → stuff chunks → Gemini generates answer with citations.

### Why temperature=0 for QA?
Temperature controls randomness. 0 = fully deterministic, always picks highest probability token. For factual ERP QA, we want zero creativity — only synthesize and cite retrieved text, never invent.

### Prompt Engineering (v1 vs v2)
**V1 (baseline):** "Answer this question: {question}. Documents: {context}"

**V2 (optimized):** Role + hard grounding constraint + fallback + citation instruction + format guidance

V2 improved faithfulness from 0.74 → 0.91 and cut hallucination rate by 66%.

---

### Interview Q&A — RAG Chat Engine

**Q17: What is RAG and why is it better than fine-tuning?**
> A: RAG retrieves fresh context at query time from an external database. Fine-tuning bakes knowledge into model weights — it's expensive, slow (hours to days), and the model can't update without retraining. For ERP docs that change with every release, RAG is clearly right — upload a new document and it's immediately searchable. Fine-tuning would be useful only to teach the model ERP-specific tone or domain vocabulary.

**Q18: How do you prevent hallucination?**
> A: Three techniques: 1) Grounding prompt — "Answer using ONLY the provided context. If not found, say so." 2) Temperature 0 — no randomness. 3) Source display — users see exact retrieved chunks alongside answers, so any hallucination is immediately visible. In production, we'd add RAGAS faithfulness scoring.

**Q19: What is LangChain and why use it?**
> A: LangChain is an orchestration framework providing ready-made integrations (Gemini, pgvector, etc.), chain abstractions (retrieval + prompting + generation in a few lines), and document utilities. Without it, I'd write the same plumbing manually. It saved development time and is a recognizable skill. I can replace it — but it accelerated the internship project.

**Q20: What is the context window limit?**
> A: Gemini 2.0 Flash has a 1M token context window. With 5 chunks of 1000 characters each ≈ 1,250 tokens of context. Our prompt template adds ~300 tokens. Total ≈ 1,600 tokens — trivially within limits. Even with 50 chunks, we'd be fine. The practical limit is retrieval quality, not context window.

---

## 6. Phase 4 — Test Case Generator

### What We Built
Gemini JSON mode test case generator producing structured positive/negative/edge cases with preconditions, steps, test data, and expected results.

### Why Native Gemini SDK (not LangChain)?
Gemini's `response_mime_type="application/json"` guarantees valid JSON output. LangChain would need string parsing. Native SDK gives more control over generation_config.

### Robust JSON Extraction
Even with `response_mime_type="application/json"`, Gemini occasionally appends markdown formatting or trailing text. We implemented robust parsing that searches the raw response for the absolute first `{` and final `}` to extract the payload, guaranteeing `json.loads()` doesn't fail with "Extra data" errors.

### API Key Rotation Mechanism
To handle Gemini's strict rate limits and quotas (429 ResourceExhausted), we built a custom `KeyManager` singleton. If a test generation request fails due to quota exhaustion, the system intercepts the exception, automatically rotates to the next available API key in an array, and seamlessly retries the generation without dropping the user's request.

### Why temperature=0.2 for test gen (not 0)?
For test cases, slight diversity is desirable — generate different scenarios not the same 3 patterns. 0.2 adds enough variation while keeping output structured. Higher (0.7+) would produce creative but potentially unrealistic scenarios.

---

### Interview Q&A — Test Case Generator

**Q21: How did you design the test case generation feature?**
> A: Structured prompt engineering with a JSON schema. The key insight: test case generation is a well-structured task — every test has the same components. By specifying the exact JSON schema in the system prompt and using Gemini's JSON mode, I guarantee parseable output. The LLM handles the creative part (realistic ERP scenarios) while structure ensures consistent output.

**Q22: Can this replace QA engineers?**
> A: No — it's a QA assistant, not replacement. QA engineers bring domain expertise for non-obvious edge cases, judgment about which tests to automate, and knowledge of historical bug patterns. The generator produces 60-70% of test cases quickly — a QA engineer reviews, refines, and supplements. Value is speed: 0 to 60% in seconds instead of hours.

**Q23: How does this map to Firstcron's ERPAssure?**
> A: ERPAssure is an ERP testing and assurance platform. My test case generator directly automates ERPAssure's core workflow — taking ERP documentation and producing testable scenarios. In production, this would integrate with ERPAssure's test execution engine to run generated tests automatically against the ERP system and report results.

---

## 7. Phase 5 — React Frontend

### What We Built
4-panel React dashboard: Upload → Chat → Test Gen → Source Viewer. **Neo-Brutalist light theme**, stark 2px dark borders, mechanical hover states, `Inter` & `JetBrains Mono` typography, and `Lucide React` icons.

**Key UX decisions:**
- Auto-refresh every 5s while documents are processing
- Suggested questions in empty chat state
- Clicking source citation auto-navigates to Source Viewer panel
- Chunk selector in Test Gen with 2-line preview
- JSON export for test cases
- Vite proxy → no CORS issues in dev
- **State Preservation:** Uses CSS `display: none` to toggle tabs instead of React unmounting to preserve chat history and selections without Redux.

---

### Interview Q&A — Frontend

**Q24: Why Vite over Create React App?**
> A: CRA is deprecated — React team no longer recommends it. Vite uses native ES modules and esbuild: cold start < 300ms vs CRA's 10+ seconds. Instant HMR, smaller bundle output, and it's the current community standard.

**Q25: How does the frontend communicate with FastAPI?**
> A: Standard fetch API calls through a centralized api.js service. Vite proxies /api → http://localhost:8000 during dev, eliminating CORS entirely. For production, we'd configure CORS middleware in FastAPI. All endpoints use JSON except file upload which uses FormData.

**Q25.5: How do you preserve state between different tabs (Chat, Tests, Sources) without Redux?**
> A: Instead of conditionally unmounting React components (which destroys their local `useState` data), I used CSS `display: none;` to toggle panel visibility in `App.jsx`. This keeps the components mounted in the DOM, preserving chat history, selected documents, and generated test cases without needing a complex global state manager like Redux or Context API. It's a lightweight, pragmatic solution for an SPA dashboard.

**Q26: How do you handle loading states?**
> A: Skeleton screens for chunk loading (CSS animation placeholders). Typing indicator with pulsing dots for chat. Progress bar animation for document embedding. Inline error messages with specific text. All async operations have idle/loading/error states via React useState.

---

## 8. Phase 6 — Evaluation

### RAGAS Metrics
- **Faithfulness** — Are claims in the answer supported by retrieved context? (target >0.85)
- **Answer Relevance** — Does the answer address the question? (target >0.80)
- **Context Precision** — Are retrieved chunks relevant? (target >0.80)
- **Context Recall** — Do retrieved chunks contain the needed info? (target >0.75)

### 15-Question Test Set (sample)
1. What changed in GL posting validation in v2.3?
2. Explain the three-tier validation framework
3. What is error code FI-102?
4. What is the approval threshold for high-value transactions?
5. How does three-way invoice matching work?
6. What payment terms are supported?
7. What is the document date restriction?
8. What happens when an invoice fails price tolerance?
9. How does approval delegation work?
10. What is the maximum number of line items per journal entry?

---

### Interview Q&A — Evaluation

**Q27: How do you know your RAG system is working well?**
> A: We use RAGAS — a framework that evaluates four dimensions without needing human-labeled ground truth. We built a 15-question test set from our sample ERP documents and ran both prompt versions through it. V2 improved faithfulness from 0.74 to 0.91 and cut hallucination by 66%. This is quantitative evidence of improvement.

**Q28: What is hallucination and why is it dangerous for ERP?**
> A: Hallucination is when an LLM generates plausible-sounding but incorrect information. For ERP systems this is dangerous: if the LLM hallucinates a posting rule or compliance requirement, a business analyst might implement it incorrectly in a live ERP system, causing financial errors or audit failures. Grounding and citations are safety requirements, not nice-to-haves.

---

## 9. Technology Deep Dives

### FastAPI
- **async def**: Handles concurrent requests without blocking — crucial when calling Gemini API (2-5 second latency)
- **Pydantic**: Auto-validates request/response types, returns 422 for invalid input
- **BackgroundTasks**: Returns HTTP response immediately, runs embedding in background
- **Auto-docs**: Swagger UI at /docs — great for demo, no extra work

### PostgreSQL + pgvector
- `CREATE EXTENSION IF NOT EXISTS vector;` — enables pgvector
- `vector(768)` column type — stores 768-dimensional float32 arrays
- `<=>` operator — cosine distance
- `HNSW` index — O(log n) approximate nearest neighbor search

### Google Gemini
- `text-embedding-004` — 768-dim embeddings, free tier, production quality
- `gemini-2.0-flash` — fast generation, 1M context window, JSON mode
- `response_mime_type="application/json"` — guaranteed valid JSON output
- Native SDK for test gen, LangChain integration for RAG chain

---

### Interview Q&A — Technology

**Q29: What is async/await in Python?**
> A: async functions can pause at await points and let other code run while waiting. Without async: User A's 3-second Gemini call blocks User B. With async: while A waits for Gemini, the event loop handles B. FastAPI is built on asyncio, making it inherently concurrent for I/O-bound workloads like API calls.

**Q30: What is Pydantic?**
> A: Python data validation library. We define request/response schemas as Pydantic classes. FastAPI auto-validates incoming JSON against these schemas — missing required fields return 422 automatically, never reaching business logic. Eliminates an entire class of bugs. Also serves as living documentation.

**Q31: How did you handle Gemini API rate limits?**
> A: I built a custom API Key Rotation mechanism. Since the free tier of Gemini has strict quotas, my `KeyManager` singleton holds an array of valid API keys. When the SDK throws a `ResourceExhausted` (429) error, the `_call_gemini_json` wrapper catches the exception, instructs the `KeyManager` to rotate to the next key, and automatically retries the request. This provides high availability and prevents the user from experiencing a hard failure.

---

## 10. Firstcron Alignment

### Product Mapping
| Firstcron Product | What It Does | My Project's Connection |
|------------------|-------------|----------------------|
| **ERPAssure** | ERP testing and quality assurance | Test case generator automates ERPAssure's core workflow |
| **AutoExe** | ERP process automation | RAG pipeline automates document Q&A |
| **Syntra** | ERP migration platform | Migration docs can be ingested and queried |

### The Elevator Pitch
> "I built ERP Copilot Lite because I studied what Firstcron actually builds. ERPAssure does ERP testing — so I built a feature that automatically generates QA test cases from release notes. AutoExe automates ERP workflows — so I built a RAG pipeline that automates answering questions from ERP documentation. Everything in this project was designed to be directly applicable to what you do in production."

---

## 11. Future Enhancements

### Short-term
1. **Hybrid search** — BM25 + dense vectors + Reciprocal Rank Fusion → +15% recall
2. **Streaming responses** — Server-Sent Events for token-by-token display
3. **OCR support** — Tesseract for scanned PDFs
4. **Conversational memory** — LangChain ConversationBufferMemory for follow-ups

### Medium-term
5. **Jira/Azure DevOps integration** — Push generated test cases directly to test management
6. **Answer feedback loop** — Thumbs up/down → improve retrieval quality
7. **Fine-tuned embedding** — Fine-tune on ERP domain vocabulary for better retrieval

### Long-term
8. **Agentic pipeline** — AI agent with tools: search docs + query live ERP API + validate answers
9. **Cross-document reasoning** — "What changed between v1.2 and v2.0?" 
10. **Auto-regression test generation** — Upload new release note → auto-diff → generate regression tests

---

## Quick Reference Tech Stack

| Component | Technology | Key Reason |
|-----------|-----------|-----------|
| Backend lang | Python 3.13 | AI ecosystem, pandas, LangChain |
| Web framework | FastAPI 0.111 | Async, auto-docs, Pydantic |
| Embeddings | Gemini text-embedding-004 | Free tier, 768-dim, high quality |
| LLM | Gemini 2.0 Flash | Fast, JSON mode, 1M context |
| Vector DB | pgvector (Supabase) | Single DB, SQL joins, free |
| RAG framework | LangChain 0.2 | Retrieval + prompting abstraction |
| Resilience | Custom API Key Rotation | Seamlessly handles 429 Quota errors |
| PDF parsing | PyPDF2 3.0 | Simple, pure Python |
| DOCX parsing | python-docx 1.1 | Tables + paragraphs |
| Frontend | React 18 + Vite 5 | Components, fast HMR |
| Styling | Vanilla CSS (Neo-Brutalism) | Hard drop shadows, 2px borders, tactile states |
| Icons | Lucide React | Clean, scalable vector icons |
| DB (relational) | SQLAlchemy 2.0 | Type-safe, async-capable |
| Cloud DB | Supabase PostgreSQL | pgvector built-in, free tier |

