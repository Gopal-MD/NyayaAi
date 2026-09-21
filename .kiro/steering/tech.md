# Tech Steering

## Stack
- Frontend: Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui, mobile-first, PWA-ready
- Backend: Python 3.11 + FastAPI + Pydantic v2
- LLM: Groq API (Llama 3.3 70B for reasoning, Llama 3.1 8B for cheap classification, Whisper for STT).
  Read model names and API key from env vars; never hardcode them.
- Embeddings: BAAI/bge-m3 (or multilingual-e5-base). Reranker: bge-reranker-base.
- Vector store: ChromaDB (persistent, precomputed index). Hybrid search: BM25 (rank_bm25) + dense.
- Doc processing: PyMuPDF, pytesseract (eng+tam+hin) fallback, python-docx
- PII: Microsoft Presidio + custom regex for Aadhaar/PAN/phone/email
- Auth: Firebase Auth (frontend) + Firebase Admin token verification (backend)
- DB: SQLite for local/dev (SQLAlchemy 2.0 + Alembic), Postgres-compatible schema
- PDF generation: WeasyPrint or ReportLab
- Deployment: frontend on Vercel, backend on Render/Railway

## Architecture rule
Use a single orchestrator with a FIXED sequential pipeline of plain Python functions.
Do NOT build autonomous multi-agent systems. Each LLM step must use structured JSON output
validated by Pydantic, with one retry on validation failure.

## Code standards
- Type hints everywhere; Pydantic models for all request/response bodies
- Separate modules: api/, orchestrator/, rag/, documents/, safety/, translation/, referrals/, models/, core/
- No secrets in code; use .env and .env.example
- Never log raw document text or PII
- Every endpoint verifies the Firebase token and scopes data by user_id
- Write pytest tests for: citation validator, safety gate, clause rules, deadline extraction, abstention
- Handle Groq rate limits with retry/backoff and a cache layer for demo documents
