# NyayaAi

**AI legal information and document understanding for India.**

NyayaAi helps people understand residential tenancy documents, identify clauses that deserve attention, find deadlines, and prepare questions for a qualified lawyer. The MVP is focused on Tamil Nadu tenancy workflows with a central baseline and supports English, Tamil, and Hindi pathways.

> NyayaAi provides legal information to help you understand and prepare. It is not legal advice and does not replace a qualified lawyer.

## What It Does

- Uploads PDF, DOCX, JPG, and PNG documents
- Extracts text with PyMuPDF, python-docx, and OCR fallback
- Masks common PII before document text is processed further
- Extracts rental-agreement facts such as rent, deposit, notice period, and lock-in period
- Flags clauses involving penalties, maintenance, termination, and subletting
- Compares two documents and reports added, removed, and modified clauses
- Provides a fixed safety gate for high-risk situations
- Supports grounded retrieval with BM25 and dense search components
- Validates citations deterministically before presenting sourced claims
- Provides a Next.js frontend with language selection, upload, and assistant screens

## Architecture

NyayaAi uses one predictable sequential pipeline rather than autonomous agents:

```text
Safety gate
  -> language detection and translation
  -> intent and jurisdiction detection
  -> missing-information check
  -> hybrid retrieval and reranking
  -> grounded generation
  -> deterministic citation validation
  -> action-plan construction
  -> output translation
```

### Repository Layout

```text
backend/
  app/
    api/             FastAPI route handlers
    core/            settings, auth, database, logging, Groq client
    documents/       extraction, PII masking, analysis, comparison
    models/          SQLAlchemy and Pydantic models
    orchestrator/    fixed pipeline and generation flow
    rag/             chunking, BM25, dense store, retrieval, citations
    safety/          risk detection and emergency resources
    translation/     language detection and translation helpers
  data/              manifests, glossary, clause rules, verified-data placeholders
  tests/
frontend/
  src/app/           Next.js App Router pages
  src/components/    providers and authentication
  src/lib/           Firebase and API clients
  src/store/         Zustand application state
.kiro/
  specs/             product requirements, design, and implementation tasks
  steering/          product and technical constraints
```

## Requirements

- Python 3.12 recommended
- Node.js 22+
- npm 10+
- Optional: Tesseract OCR installed and available on `PATH` for image-based documents
- Firebase project for authentication
- Groq API key for LLM classification, generation, translation, and voice features

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Gopal-MD/NyayaAi.git
cd NyayaAi
```

### 2. Configure the backend

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Set the required values in `backend/.env` locally. Never commit that file.

```env
GROQ_API_KEY=your_groq_api_key
FIREBASE_PROJECT_ID=your_firebase_project_id
DATABASE_URL=sqlite+aiosqlite:///./nyayasaathi.db
ALLOWED_ORIGINS=http://localhost:3000
```

For local development, SQLite is already configured. Use a Postgres URL and persistent storage for a hosted backend.

### 3. Configure the frontend

```powershell
Copy-Item frontend\.env.example frontend\.env.local
```

Set the Firebase web configuration and backend URL in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_web_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_firebase_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=your_measurement_id
```

Firebase web configuration values are intended for frontend configuration, but API keys and service credentials must still be managed through the hosting platform and Firebase restrictions.

## Run Locally

Start the backend from the repository root:

```powershell
cmd /c "cd /d backend && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001"
```

Start the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev -- --port 3000
```

Open:

- Application: http://localhost:3000
- Backend API: http://127.0.0.1:8001
- Swagger UI: http://127.0.0.1:8001/docs
- Health check: http://127.0.0.1:8001/health

## Validation

Backend tests:

```powershell
cd backend
..\.venv\Scripts\python -m pytest -q
```

Frontend production build:

```powershell
cd frontend
npm run build
```

Backend import and compile check:

```powershell
cd backend
..\.venv\Scripts\python -m compileall -q app
..\.venv\Scripts\python -c "from app.main import app; print(app.title)"
```

## User Workflow

### 1. Start a session

The user opens the Next.js application, chooses English, Tamil, or Hindi, and signs in with Firebase or continues as a guest where the configured flow allows it.

### 2. Create or select a case

The user creates a tenancy case and provides the relevant state or jurisdiction. Case records and child records are scoped to the authenticated Firebase user.

### 3. Upload a document

The user accepts the privacy consent statement and uploads a PDF, DOCX, JPG, or PNG file. The backend validates the file type and size before processing it.

### 4. Extract and protect the text

NyayaAi extracts text with PyMuPDF or python-docx. Image-based documents use OCR when text density is low. Aadhaar numbers, PAN numbers, email addresses, and phone numbers are masked before the text is stored or sent to an LLM.

### 5. Analyse the agreement

The analysis pipeline classifies the document, extracts structured rental facts, finds deadlines, identifies relevant clauses, and prepares a plain-language summary with questions the user can ask a lawyer.

### 6. Ask a question

The user asks a question in the assistant. The backend detects safety risk, language, intent, and jurisdiction before searching the document and official-source context.

### 7. Receive a grounded response

The answer generator can only use retrieved context. Each citation is checked against source text by deterministic validation. If the answer cannot be verified, NyayaAi returns an abstention message instead of guessing.

### 8. Handle urgent situations

If the safety gate detects arrest, immediate danger, domestic violence, child safety concerns, self-harm, or another high-risk signal, normal answer generation is bypassed. The response shows emergency and legal-aid resources instead.

### 9. Prepare next steps

The action-plan layer turns verified facts, deadlines, documents, official resources, and lawyer questions into a practical checklist. It always includes the legal-information limitation.

## Developer Workflow

```text
Create or update code
  |
  v
Run backend tests and frontend build
  |
  v
Check that no .env files or secrets are staged
  |
  v
Commit to main
  |
  v
Push to GitHub
  |
  v
Vercel builds frontend from frontend/
  |
  v
Backend host runs FastAPI from backend/
```

For a new feature, keep changes in the owning layer: route contracts in `api/`, legal processing in `documents/`, orchestration in `orchestrator/`, retrieval in `rag/`, and UI behavior in `frontend/src/`. Add focused tests for safety, citations, extraction, deadlines, and abstention before widening the change.

## Deployment

### Vercel frontend

1. Import `Gopal-MD/NyayaAi` into Vercel.
2. Set the project root to `frontend`.
3. Use the default Next.js build settings.
4. Add the `NEXT_PUBLIC_*` variables from `frontend/.env.example` in the Vercel project settings.
5. Set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL.

### Backend

Deploy `backend` to Render, Railway, or another Python-compatible host.

- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Configure all backend environment variables in the provider dashboard.
- Use persistent storage for SQLite, ChromaDB, BM25 indexes, and model caches, or move production data to managed services.
- Update `ALLOWED_ORIGINS` to the deployed Vercel URL.

## Data and Safety Notes

- Do not commit `.env`, `.env.local`, Firebase service-account JSON, API keys, model caches, databases, or uploaded documents.
- Source and emergency data containing `TODO_VERIFY` are placeholders and must be replaced with verified official information before production use.
- High-risk messages should bypass normal generation and surface emergency or legal-aid resources.
- Legal claims must be supported by document or official-source citations; otherwise the system should abstain.
- The application is an information and preparation tool, not a lawyer, court, or emergency service.

## Current MVP Scope

The current implementation provides the backend application shell, document-processing foundation, citation validation, safety resources, frontend upload and assistant screens, Firebase wiring, and deployment configuration guidance. Production hardening still requires verified legal datasets, full Firebase Admin credentials, authenticated end-to-end flows, persistent hosted storage, and expanded automated coverage.

## License

No license has been selected yet. Add an appropriate license before accepting external contributions or distributing the project publicly.
