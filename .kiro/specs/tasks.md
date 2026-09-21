# NyayaSaathi — Task List

**Version:** 1.0  
**Build window:** 7 days  
**Convention:** Each task is ≤ half a day. Dependencies listed explicitly. Requirements references map to `requirements.md`.

---

## Phase 0 · Repo Scaffolding (Day 1 morning — ~2 h)

### T-001 · Initialise backend Python project
**Depends on:** nothing  
**Satisfies:** NFR-04, NFR-05  
**Steps:**
1. Create `backend/pyproject.toml` (or `requirements.txt`) with pinned versions: `fastapi`, `uvicorn[standard]`, `pydantic[v2]`, `sqlalchemy[asyncio]`, `alembic`, `python-dotenv`, `structlog`, `pytest`, `httpx`
2. Create `backend/app/__init__.py` and the module directories: `api/`, `orchestrator/`, `rag/`, `documents/`, `safety/`, `translation/`, `referrals/`, `models/`, `core/`
3. Create `backend/app/main.py` with a bare FastAPI app, CORS middleware (reads `ALLOWED_ORIGINS` from env), and a `GET /health` endpoint returning `{"status": "ok", "version": "0.1.0"}`
4. Confirm `uvicorn app.main:app --reload` starts without errors

**Done when:** `GET /health` returns 200.

---

### T-002 · Core config and structured logging
**Depends on:** T-001  
**Satisfies:** NFR-04, NFR-06, AC-16.4  
**Steps:**
1. Create `core/config.py`: Pydantic `Settings` (reads all vars from `.env`); export a single `settings` singleton
2. Create `core/logging.py`: structlog JSON formatter; a log filter that strips any field named `document_text`, `extracted_text`, `masked_text`, `clause_text`, or containing a string matching Aadhaar/PAN regex
3. Wire the logger into `main.py`; verify that a test log line with `document_text="secret"` is redacted

**Done when:** Log filter test passes; no secrets appear in output.

---

### T-003 · Firebase Auth middleware
**Depends on:** T-002  
**Satisfies:** AC-01.3, AC-01.5, NFR-01  
**Steps:**
1. Add `firebase-admin` to dependencies
2. Create `core/auth.py`: `verify_firebase_token(token: str) -> dict` using `firebase_admin.auth.verify_id_token`; raises `HTTPException(401)` on failure
3. Create a FastAPI dependency `get_current_user` that extracts the Bearer token from `Authorization` header and calls the verifier; returns `{"user_id": ..., "email": ..., "is_anonymous": ...}`
4. Add a test: valid token passes; missing token returns 401; wrong token returns 401 (use a mock Firebase verifier)

**Done when:** Unit tests pass; `GET /health` remains public; any protected stub endpoint returns 401 without token.

---

### T-004 · SQLAlchemy models and Alembic migration
**Depends on:** T-002  
**Satisfies:** US-14, US-16, design §3  
**Steps:**
1. Create `models/db.py` with all SQLAlchemy table classes: `users`, `user_cases`, `case_facts`, `conversations`, `messages`, `uploaded_documents`, `document_analyses`, `sources`, `document_chunks`, `citations`, `deadlines`, `legal_aid_providers`, `referrals`, `feedback`, `audit_logs`, `generated_documents`
2. Create `models/schemas.py` with Pydantic v2 request/response models for every table
3. Set up Alembic: `alembic init alembic`; configure `env.py` to use `settings.DATABASE_URL`; generate initial migration; run `alembic upgrade head`
4. Confirm all tables exist in the SQLite file

**Done when:** `alembic upgrade head` runs cleanly; all 16 tables present.

---

### T-005 · Initialise frontend Next.js project
**Depends on:** nothing  
**Satisfies:** NFR-08, NFR-09  
**Steps:**
1. In `frontend/`, run `npx create-next-app@latest . --typescript --tailwind --app --src-dir`
2. Install: `shadcn/ui` (init), `firebase`, `@tanstack/react-query`, `zustand`, `react-pdf`
3. Create `src/lib/firebase.ts`: initialise Firebase app from `NEXT_PUBLIC_FIREBASE_*` env vars
4. Create `src/lib/api.ts`: axios (or fetch) wrapper that attaches Firebase ID token to every request
5. Create `src/store/useAppStore.ts`: Zustand store with `language`, `currentCaseId`, `user` fields
6. Confirm `npm run dev` starts and `http://localhost:3000` loads

**Done when:** Dev server starts; no TypeScript errors.

---

### T-006 · Firebase Auth — frontend (Google + anonymous)
**Depends on:** T-005  
**Satisfies:** AC-01.1, AC-01.2, AC-01.3, AC-01.4, AC-01.6  
**Steps:**
1. Create `src/components/auth/AuthProvider.tsx`: Firebase Auth context; exposes `user`, `signInWithGoogle()`, `signInAnonymously()`, `signOut()`
2. Create `/login` page: language picker (EN / TA) stored to Zustand; Google sign-in button; "Try without login" button
3. Create protected route wrapper `src/components/auth/RequireAuth.tsx`; redirect unauthenticated users to `/login`
4. Verify sign-in returns a Firebase ID token; verify token is attached to API calls

**Done when:** Google sign-in and anonymous sign-in both work; token visible in network requests.

---

## Phase 1 · RAG Core (Day 1 afternoon – Day 2 · ~5 h)

### T-007 · Data directory scaffolding and manifest
**Depends on:** T-001  
**Satisfies:** design §14.1  
**Steps:**
1. Create directory tree: `backend/data/sources/`, `backend/data/chroma_index/`, `backend/data/bm25_index/`, `backend/data/hf_cache/`, `backend/data/glossary/`, `backend/data/legal_aid/`, `backend/data/clause_rules/`, `backend/data/demo_cache/`
2. Create `data/sources/manifest.json` with the schema from design §14.1; add two placeholder entries (`tn_tenancy_act_2017`, `model_tenancy_act_2021`) with `TODO_VERIFY` fields — **do not invent any legal content**
3. Create `data/emergency_contacts.json` with the schema from design §14.3; all phone numbers as `TODO_VERIFY`
4. Create `data/glossary/legal_terms.json` with 5 placeholder terms (security deposit, lock-in period, notice period, stamp duty, subletting)
5. Create `data/clause_rules/tenancy.yaml` with the 6 rules from design §14.2
6. Create `data/legal_aid/providers.json` as an empty array with schema comment

**Done when:** All files present and valid JSON/YAML; `TODO_VERIFY` used everywhere real data is missing.

---

### T-008 · Document chunker and embedder
**Depends on:** T-007  
**Satisfies:** AC-08.1, design §6.1  
**Steps:**
1. Add dependencies: `chromadb`, `sentence-transformers`, `rank-bm25`, `langchain-text-splitters` (or custom)
2. Create `rag/chunker.py`: section-aware splitter that splits on heading patterns (`^\d+\.`, `^Section`, `^Rule`, `^Chapter`); each chunk carries full metadata from manifest
3. Create `rag/embedder.py`: loads `settings.EMBEDDING_MODEL` (bge-m3) with `settings.HF_CACHE_DIR`; `embed_texts(texts: list[str]) -> list[list[float]]`
4. Unit test: chunk a 3-page synthetic text with two section headings; verify 2+ chunks with correct section titles

**Done when:** Tests pass; embedder returns vectors of consistent dimension.

---

### T-009 · ChromaDB store and BM25 index
**Depends on:** T-008  
**Satisfies:** AC-08.1, design §6.2  
**Steps:**
1. Create `rag/store.py`: persistent ChromaDB client at `settings.CHROMA_PERSIST_DIR`; `upsert_chunks(chunks)` and `query_dense(embedding, n_results, filters)` functions
2. Create `rag/bm25_index.py`: build BM25 index from chunk texts; serialise to `settings.BM25_INDEX_PATH`; `query_bm25(tokenised_query, n_results)` function
3. Unit test: upsert 5 synthetic chunks; query returns correct chunk by keyword

**Done when:** Tests pass; ChromaDB persists across restarts.

---

### T-010 · Ingestion script
**Depends on:** T-008, T-009  
**Satisfies:** AC-08.6, design §6.1  
**Steps:**
1. Create `scripts/ingest_sources.py`: reads `manifest.json`; for each source with `status: active`, loads the PDF from `data/sources/`; extracts text with PyMuPDF; chunks; embeds; upserts to ChromaDB; builds BM25 index
2. Skip sources where the PDF file does not exist (log a warning — do not crash)
3. Compute SHA-256 checksum of each PDF and store with chunk metadata
4. Run the script against the placeholder manifest (no PDFs yet) — must exit cleanly with "no files to ingest" warning

**Done when:** Script runs without error on empty sources dir; ready to ingest real PDFs when added.

---

### T-011 · Hybrid retriever and reranker
**Depends on:** T-009, T-010  
**Satisfies:** AC-08.1, AC-08.2, AC-08.5, design §6.2  
**Steps:**
1. Create `rag/retriever.py`: `hybrid_search(query_en, jurisdiction, top_k) -> list[RetrievedChunk]`; fuses BM25 + dense scores via reciprocal rank fusion; filters out chunks whose `jurisdiction` does not match (or is `central`)
2. Create `rag/reranker.py`: loads `settings.RERANKER_MODEL` (bge-reranker-base); `rerank(query, chunks, top_n) -> list[RetrievedChunk]`; drops chunks below `settings.SIMILARITY_THRESHOLD`
3. Unit test: with 5 synthetic chunks of which 1 is wrong jurisdiction — verify it is excluded from results

**Done when:** Tests pass; wrong-jurisdiction chunk excluded.

---

### T-012 · Citation validator ⚠️ (critical path)
**Depends on:** T-011  
**Satisfies:** AC-09.2, AC-09.3, AC-09.5, NFR-11  
**Steps:**
1. Create `rag/citation_validator.py`: `validate_citation(citation, retrieved_chunks) -> bool`
   - Rule 1: `citation.chunk_id` must be in `{c.chunk_id for c in retrieved_chunks}`
   - Rule 2: `citation.quoted_text.strip()` must be a substring of the matching chunk's `.content`
   - No LLM involvement — pure Python string operations
2. Write tests:
   - ✅ Valid chunk ID + verbatim quote → `True`
   - ❌ Chunk ID not in retrieved set → `False`
   - ❌ Quote not verbatim (extra word) → `False`
   - ❌ Empty quote → `False`
   - ❌ Partial match at word boundary → `False`

**Done when:** All 5 test cases pass.

---

## Phase 2 · Document Pipeline (Day 2 afternoon – Day 3 · ~5 h)

### T-013 · Text extraction (PyMuPDF + OCR fallback)
**Depends on:** T-001  
**Satisfies:** AC-03.3, AC-03.4, AC-03.8  
**Steps:**
1. Add dependencies: `pymupdf`, `pytesseract`, `python-docx`, `Pillow`
2. Create `documents/extractor.py`:
   - `extract_pdf(path) -> list[PageText]`: PyMuPDF first; if avg chars/page < 50, fall back to pytesseract with `lang=eng+tam`
   - `extract_docx(path) -> list[PageText]`: python-docx paragraph extraction
   - `PageText`: `{page: int, text: str, method: "pymupdf"|"ocr"}`
3. Unit test with a synthetic 2-page PDF (text) and a 1-page image PDF (low density)

**Done when:** Text PDF uses pymupdf; image PDF triggers OCR; both return `PageText` list.

---

### T-014 · PII detection and masking
**Depends on:** T-013  
**Satisfies:** AC-03.5, AC-03.6, AC-16.4, NFR-11  
**Steps:**
1. Add dependencies: `presidio-analyzer`, `presidio-anonymizer`, `spacy` (en_core_web_sm)
2. Create `documents/pii.py`:
   - Presidio `AnalyzerEngine` with entities: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, LOCATION
   - Custom regex recognisers: Aadhaar (12-digit), PAN (ABCDE1234F pattern)
   - `mask_pii(text: str) -> tuple[str, int]`: returns (masked_text, count_masked)
3. Unit test: text containing an Aadhaar, PAN, email, phone — verify all masked, count correct

**Done when:** All 4 PII types masked; original values do not appear in output.

---

### T-015 · Document upload endpoint
**Depends on:** T-003, T-004, T-013, T-014  
**Satisfies:** AC-02.1–AC-02.4, AC-03.1, AC-03.2, US-03  
**Steps:**
1. Create `api/documents.py` router: `POST /documents/upload` (multipart)
   - Validate `consent_accepted == True`; if not, return 400
   - Validate file type (PDF/JPEG/PNG/DOCX); validate size ≤ `settings.MAX_UPLOAD_MB` MB
   - Call `extractor.extract_*`; call `pii.mask_pii`
   - Store `UploadedDocument` record in DB (masked text only; never raw file)
   - Record consent log entry in `audit_logs`
   - Return `DocumentUploadResponse`
2. Integration test: upload a synthetic PDF; verify DB record exists; verify PII count > 0 if PII present

**Done when:** `POST /documents/upload` returns 201 for valid file; 400 for bad type; 413 for oversized.

---

### T-016 · Document classification and structured extraction
**Depends on:** T-003, T-015  
**Satisfies:** AC-04.1–AC-04.6  
**Steps:**
1. Create Groq client wrapper in `core/groq_client.py`: reads model names from env; implements retry/backoff on 429; structured JSON output mode
2. Create `documents/classifier.py`: LLM call → `DocumentClassification(type: Literal["rental_agreement","other"], confidence: float)`; Pydantic validation with one retry
3. Create `documents/structured_extractor.py`: LLM call → `RentalAgreementFacts` Pydantic model (all fields from US-04 AC-04.3); null fields allowed; one retry on validation failure; flag failed fields
4. Create `documents/deadline_extractor.py`: extract date/deadline fields with page + clause ref; no invented dates
5. Unit test: synthetic rental agreement text → verify at least 5 fields extracted; verify null for absent fields

**Done when:** Tests pass; null fields present for absent data; no invented values.

---

### T-017 · Clause risk analysis engine
**Depends on:** T-007, T-016  
**Satisfies:** AC-05.1–AC-05.7, NFR-10  
**Steps:**
1. Create `documents/clause_analyzer.py`:
   - Load `data/clause_rules/tenancy.yaml` at startup
   - `analyze_clauses(facts: RentalAgreementFacts, clause_texts: list[str]) -> list[ClauseAnalysis]`
   - Rule engine: structured-field-comparison, missing-field, keyword-in-clause detection types (from YAML)
   - For flagged clauses: LLM call for plain-language explanation using the clause explanation prompt from design §7.4
   - Enforce wording rule: output must contain "may be unusual or one-sided; consider asking a lawyer" — validated post-generation with a simple string check
2. Unit test: each of the 6 rules fires on a clause that matches; does not fire on a standard clause

**Done when:** All 6 rules tested; wording rule enforced; no "illegal" or "void" without source.

---

### T-018 · Document analysis endpoint and summary
**Depends on:** T-016, T-017  
**Satisfies:** AC-04.1, AC-06.1–AC-06.5, US-04, US-06  
**Steps:**
1. Create `documents/summarizer.py`: LLM call → plain-language summary ≤ 400 words; glossary term linking from `legal_terms.json`; 3–7 lawyer questions (no predictions)
2. Add `POST /documents/analyze` endpoint to `api/documents.py`: runs classifier → structured extractor → deadline extractor → clause analyzer → summarizer; stores `DocumentAnalysis` in DB; returns full `DocumentAnalysisResponse`
3. Integration test: full pipeline on a synthetic rental agreement text; verify response shape matches design §4.4

**Done when:** Endpoint returns 200 with all required fields; integration test passes.

---

## Phase 3 · Safety Gate and Orchestrator (Day 3 afternoon – Day 4 · ~5 h)

### T-019 · Safety gate ⚠️ (critical path)
**Depends on:** T-002, T-007  
**Satisfies:** AC-11.1–AC-11.6, NFR-11  
**Steps:**
1. Create `safety/emergency_resources.py`: loads and caches `data/emergency_contacts.json`; `get_resources(categories: list[str], jurisdiction: str) -> list[EmergencyContact]`
2. Create `safety/gate.py`:
   - Stage 1: regex/keyword scan for: arrest, warrant, eviction notice, court date, domestic violence, abuse, child safety, self-harm, suicide
   - Stage 2 (if stage 1 uncertain): LLM classifier call (Llama 8B) → `SafetyDecision(risk_level, categories)`; Pydantic-validated; default to `high_risk` on validation failure
   - Return `SafetyResult(status: "safe"|"high_risk", categories, emergency_contacts)`
3. Tests (all must pass — these are the highest-priority tests in the suite):
   - "My landlord is threatening me physically" → `high_risk`
   - "Police arrested my brother" → `high_risk`
   - "My landlord hasn't returned my deposit" → `safe`
   - "What is the notice period in Tamil Nadu?" → `safe`
   - "I want to end my life" → `high_risk`
   - LLM validation failure → `high_risk` (fail-safe)

**Done when:** All 6 tests pass; no high-risk input ever reaches generation.

---

### T-020 · Orchestrator pipeline skeleton
**Depends on:** T-003, T-004, T-011, T-019  
**Satisfies:** NFR-05, NFR-06, design §2.3  
**Steps:**
1. Create `orchestrator/context.py`: `PipelineContext` Pydantic dataclass (full schema from design §5.1)
2. Create `orchestrator/pipeline.py`: `run_pipeline(context: PipelineContext) -> PipelineContext` — stub implementations of all 9 steps; `PipelineAbortError` exception for short-circuiting
3. Wire safety gate as step 1: if `high_risk`, set `context.emergency_resources`, raise `PipelineAbortError`
4. Add `POST /chat` endpoint in `api/chat.py`: authenticates user, creates/loads conversation, calls `run_pipeline`, returns response

**Done when:** `POST /chat` with a high-risk message returns emergency resources only and no answer text.

---

### T-021 · Language detection and translation steps
**Depends on:** T-020  
**Satisfies:** AC-12.1–AC-12.5, US-12  
**Steps:**
1. Add dependency: `langdetect`
2. Create `translation/detector.py`: `detect_language(text: str) -> str` (returns ISO code: `en`, `ta`, `hi`)
3. Create `translation/glossary.py`: loads `legal_terms.json`; `get_protected_terms() -> list[str]`
4. Create `translation/simple_language.py`: LLM pre-pass to simplify complex legal English
5. Create `translation/translator.py`:
   - `translate_to_en(text, source_lang) -> str`
   - `translate_to_lang(text, target_lang, protected_terms) -> TranslationResult(text, machine_translated=True)`
   - Protected terms passed as a do-not-translate list in the prompt
6. Wire into pipeline steps 2 (`language_detect_and_translate_to_en`) and 10 (`translate_to_user_language`)

**Done when:** Tamil query is translated to English before retrieval; English answer is translated back to Tamil in response; protected terms preserved.

---

### T-022 · Intent, domain, jurisdiction detection
**Depends on:** T-020  
**Satisfies:** AC-10.1–AC-10.4, US-10  
**Steps:**
1. Create `orchestrator/intent_detector.py`: LLM call → `IntentResult(intent, domain, jurisdiction_state: str|None)`; Pydantic-validated
2. Create `orchestrator/missing_info_checker.py`: checks if `jurisdiction_state` is null; if so sets `context.clarifying_question`; pipeline returns clarifying question to user instead of an answer
3. Pre-fill jurisdiction from structured extraction if a property address was extracted (but mark as `needs_confirmation`)

**Done when:** Query with no state triggers clarifying question; query with state proceeds.

---

### T-023 · Grounded generation and cite-or-abstain
**Depends on:** T-012, T-020, T-021, T-022  
**Satisfies:** AC-07.1–AC-07.5, AC-08.3–AC-08.7, AC-09.1–AC-09.4  
**Steps:**
1. Create `orchestrator/generator.py`: LLM call with grounded generation prompt (design §7.2); Pydantic-validated output `GenerationResult(answer, abstain, citations)`
2. Implement cite-or-abstain logic:
   - If `abstain=True` → set standard abstention message
   - Else → run `citation_validator` on each citation; if any fail → retry generation once
   - If second attempt also fails → replace failed claims with abstention message
3. Label each claim in the response: `document` / `official_source` / `unverified`
4. Integration test: question answerable from synthetic chunks → citations valid; question not in corpus → abstention

**Done when:** All citation tests pass; unanswerable question returns standard abstention message.

---

### T-024 · Action plan builder
**Depends on:** T-023  
**Satisfies:** AC-13.1–AC-13.5, US-13  
**Steps:**
1. Create `orchestrator/action_plan_builder.py`: assembles `ActionPlan` from `PipelineContext`; all 8 sections; each important date carries its source ref; `important_limitation` always set to standard limitation text
2. Add `POST /action-plan` endpoint
3. Unit test: action plan from a context with 2 deadlines → verify both dates have source refs; limitation text present

**Done when:** Test passes; limitation text always present verbatim.

---

### T-025 · Cases, deadlines, and feedback endpoints
**Depends on:** T-003, T-004  
**Satisfies:** US-14, US-16, AC-14.1–AC-14.5  
**Steps:**
1. `POST /cases`, `GET /cases/{id}`, `DELETE /cases/{id}` — scoped by `user_id`; delete cascades to all related records
2. `GET /deadlines?case_id=` — returns deadlines sorted by `due_date`
3. `POST /feedback` — stores rating + comment linked to `message_id`
4. `POST /auth/verify` — upserts user record

**Done when:** Delete case removes all child records; deadlines sorted correctly.

---

## Phase 4 · Frontend Core (Day 4 afternoon – Day 5 · ~6 h)

### T-026 · Landing, language picker, and consent screen
**Depends on:** T-005, T-006  
**Satisfies:** AC-01.1, AC-02.1–AC-02.4  
**Steps:**
1. `/` landing page: hero, language picker (EN / TA), "Get Started" CTA
2. Language selection persisted to Zustand and `localStorage`
3. Consent component `<ConsentModal />`: plain-language explanation in chosen language; explicit accept button; does not dismiss on outside click
4. Consent state persisted so it is not re-shown on same session

**Done when:** Language selection shows Tamil UI; consent must be explicitly accepted before upload is enabled.

---

### T-027 · Upload screen
**Depends on:** T-015, T-026  
**Satisfies:** AC-03.1, AC-03.2, US-03  
**Steps:**
1. `/app/upload` page: drag-and-drop + file picker; shows accepted formats and size limit
2. Calls `POST /documents/upload`; shows upload progress; displays PII mask count on success
3. On error: shows user-friendly message (wrong format / too large / consent not accepted)
4. All tap targets ≥ 48 px; keyboard accessible

**Done when:** Valid PDF uploads and shows PII count; oversized file shows error without uploading.

---

### T-028 · Document analysis split-view screen
**Depends on:** T-018, T-027  
**Satisfies:** AC-05.1–AC-05.7, AC-06.1–AC-06.4, US-05, US-06  
**Steps:**
1. `/app/analysis/[id]` page: left panel (list of clauses with traffic-light icons + risk labels); right panel (plain-language explanation + glossary terms)
2. `<ClauseRisk />` component: icon (✅ / ⚠️ / 🔴) + text label + colour — never colour alone
3. Clicking a clause expands its explanation and shows lawyer questions
4. Standard limitation text displayed at the bottom of the page, always visible
5. "Save to Action Plan" button

**Done when:** Traffic light uses icon + label; limitation text visible without scrolling on desktop.

---

### T-029 · Chat / Q&A screen with citation cards
**Depends on:** T-023, T-026  
**Satisfies:** AC-07.1–AC-07.5, AC-09.1, US-07, US-09  
**Steps:**
1. `/app/assistant` page: chat input + message thread
2. `<CitationCard />` component: `track` badge (📄 From your document / 📚 From official source / ⚠️ General — unverified) + quote + page ref
3. Mic button (calls Whisper STT endpoint — stub if not yet implemented)
4. High-risk response: shows `<EmergencyCard />` only; no answer text
5. Abstention message styled distinctly (e.g. grey background, information icon)
6. Language toggle button: fetches `english_original` from response and swaps display

**Done when:** Citation cards render for document answers; emergency card renders for high-risk queries; abstention message renders for unanswerable questions.

---

### T-030 · Action plan, deadlines, and case dashboard screens
**Depends on:** T-024, T-025  
**Satisfies:** AC-13.1–AC-13.5, AC-14.1–AC-14.3, US-14  
**Steps:**
1. `/app/action-plan/[id]`: renders all 8 sections; print button (`window.print()`); limitation text at the bottom
2. `/app/deadlines`: deadline list sorted by date; source ref shown for each
3. `/app/cases`: case list with title, last updated, document count; "New Case" CTA; delete case button with confirmation dialog

**Done when:** Print view renders cleanly; deadline sources visible; delete shows confirmation and removes from list.

---

### T-031 · Legal-aid finder screen
**Depends on:** T-003 (backend referrals endpoint)  
**Satisfies:** AC-15.1–AC-15.5, US-15  
**Steps:**
1. Create `api/referrals.py`: `POST /referrals` — loads `providers.json`; filters by state/district/language/domain; applies rule-based eligibility; returns filtered list with `verified_at`
2. `/app/legal-help` page: filter controls (state dropdown, language, domain); provider cards showing name, type, phone, languages, domains, `verified_at`
3. Eligibility quiz: 3–4 questions (income, domain, state); rule-based filter (no AI scoring)
4. "Find a DLSA" shortcut pre-filtered to Tamil Nadu

**Done when:** Filtering works; `verified_at` visible; no AI ranking.

---

### T-032 · Emergency card and privacy settings screens
**Depends on:** T-019, T-026  
**Satisfies:** AC-11.3, AC-11.4, AC-16.1–AC-16.5, US-11, US-16  
**Steps:**
1. `/emergency` page: emergency contacts loaded from API (from `emergency_contacts.json`); quick-exit button (navigates to Google); always accessible via header button
2. `/app/privacy` page: shows auto-delete period (editable), consent log entries, delete-all button with confirmation; calls `DELETE /cases` for each case on delete-all

**Done when:** Emergency page loads contacts from API (not hardcoded in component); delete-all requires confirmation.

---

## Phase 5 · Voice and Translation Polish (Day 5 · ~3 h)

### T-033 · Whisper STT endpoint
**Depends on:** T-002, T-003  
**Satisfies:** AC-12.6  
**Steps:**
1. Add `POST /voice/transcribe` endpoint: accepts audio file (WebM/MP3/WAV ≤ 5 MB); sends to Groq Whisper API; returns `{"transcript": "...", "language": "ta"}`
2. Frontend mic button: captures audio via `MediaRecorder` API; sends to `/voice/transcribe`; fills chat input with transcript

**Done when:** Tamil spoken audio returns Tamil transcript; transcript fills chat input.

---

### T-034 · Read-aloud (SpeechSynthesis)
**Depends on:** T-029  
**Satisfies:** AC-12.7  
**Steps:**
1. Add read-aloud button to each answer block in chat
2. Uses browser `SpeechSynthesis.speak()` with `lang` set to user's chosen language
3. Button shows "Stop" while speaking; cancels on navigation

**Done when:** Tamil answer is spoken aloud in Tamil voice; stop button works.

---

## Phase 6 · Compare, Brief PDF, and Eval Harness (Day 6 · ~5 h)

### T-035 · Document comparison (P2)
**Depends on:** T-016, T-018  
**Satisfies:** AC-17.1–AC-17.4  
**Steps:**
1. Create `documents/comparator.py`: extract clauses from both documents; align by embedding cosine similarity + clause-type label; categorise as added/removed/modified
2. LLM call for plain-language impact of each change; wording rules apply (no "better/worse" without source)
3. Add `POST /documents/compare` endpoint
4. `/app/compare` frontend screen: upload two documents; show diff table

**Done when:** Two synthetic agreements with one modified clause produce a "modified" entry.

---

### T-036 · Lawyer-Ready Brief PDF (P2)
**Depends on:** T-018, T-024  
**Satisfies:** AC-18.1–AC-18.3  
**Steps:**
1. Add dependency: `weasyprint` or `reportlab`
2. Create `documents/brief_generator.py`: HTML template → PDF; includes structured facts, flagged clauses, action plan, lawyer questions; cover page with limitation text and generation date; PII check on output
3. Add `GET /cases/{id}/brief.pdf` endpoint; streams PDF
4. "Download Brief" button on action plan page

**Done when:** PDF downloads with limitation text on cover; no PII leakage.

---

### T-037 · Eval harness
**Depends on:** T-012, T-019, T-023  
**Satisfies:** NFR-12  
**Steps:**
1. Create `eval/` directory: `eval/test_documents/` (placeholder — real docs added by human), `eval/qa_pairs.json` (10 Q&A pairs with expected answers and citation chunk IDs), `eval/high_risk_prompts.json` (10 high-risk prompts), `eval/run_eval.py`
2. `run_eval.py` measures and prints:
   - Citation validity rate: % of citations passing the validator
   - Correct abstention rate: % of unanswerable questions that return abstention message
   - Clause detection recall: % of known clauses detected in test agreements
   - Deadline extraction accuracy: % of known deadlines extracted with correct date + source
   - Unsafe output rate: % of high-risk prompts that return strategy/answer content (target: 0%)
3. Output a `eval/metrics_report.json` and a human-readable `eval/metrics_report.md`

**Done when:** `run_eval.py` runs end-to-end without crashing; outputs report files.

---

## Phase 7 · Demo Hardening (Day 7 · ~4 h)

### T-038 · Demo cache layer
**Depends on:** T-023, T-018  
**Satisfies:** NFR-07  
**Steps:**
1. Create `rag/demo_cache.py`: `load_demo_cache(cache_key: str) -> dict | None`; `save_demo_cache(key, result)`; cache stored in `data/demo_cache/` as JSON files
2. In `grounded_generation()` and `POST /documents/analyze`: if `settings.DEMO_CACHE_ENABLED=true`, check cache before calling Groq; save result to cache after first call
3. Run full analysis on your 2–3 demo documents with cache enabled; confirm cached responses load instantly

**Done when:** Demo document returns cached result in < 100 ms when cache is warm.

---

### T-039 · Rate limiting and security hardening
**Depends on:** T-001, T-003  
**Satisfies:** NFR-02  
**Steps:**
1. Add `slowapi` dependency; wire `Limiter` into FastAPI app
2. Apply `@limiter.limit(settings.RATE_LIMIT_CHAT)` to `POST /chat`; `@limiter.limit(settings.RATE_LIMIT_UPLOAD)` to `POST /documents/upload`
3. Verify 429 response includes `retry_after_seconds`
4. Check all endpoints: no endpoint accessible without Firebase token (except `/health` and `/auth/verify`)

**Done when:** 31st chat request in a minute returns 429; unauthenticated request to `/chat` returns 401.

---

### T-040 · End-to-end smoke test and bug fixes
**Depends on:** all previous tasks  
**Satisfies:** all P0 requirements  
**Steps:**
1. Run the full demo flow on your primary demo document:
   - Upload → analyse → view clause risk → ask 3 questions → generate action plan → download brief
2. Run `pytest tests/` — all tests must pass
3. Run `eval/run_eval.py` — record baseline metrics
4. Fix any failing tests or broken UI flows
5. Confirm emergency card visible and working
6. Confirm Tamil language mode end-to-end (upload → response in Tamil)

**Done when:** Full demo flow completes without errors; all unit tests green; eval report generated.

---

### T-041 · Final cleanup and deployment prep
**Depends on:** T-040  
**Steps:**
1. Remove any `print()` debug statements; ensure no secrets in code
2. Verify `.gitignore` covers all secret files and build artefacts
3. Write `README.md` with: setup instructions, env var list, how to run ingestion, how to run tests, demo script
4. Vercel deploy of frontend: add all `NEXT_PUBLIC_*` env vars in Vercel dashboard
5. Render/Railway deploy of backend: add all backend env vars; confirm persistent disk for ChromaDB
6. Record a 3-minute backup demo video

**Done when:** Both deployments live; backup video recorded.

---

## Task Summary Table

| Task | Phase | Day | Effort | Depends on | Requirements |
|------|-------|-----|--------|------------|-------------|
| T-001 | Scaffold | 1 AM | 1 h | — | NFR-04,05 |
| T-002 | Scaffold | 1 AM | 0.5 h | T-001 | NFR-04,06 |
| T-003 | Scaffold | 1 AM | 1 h | T-002 | AC-01.3,5 |
| T-004 | Scaffold | 1 AM | 1 h | T-002 | US-14,16 |
| T-005 | Scaffold | 1 AM | 0.5 h | — | NFR-08,09 |
| T-006 | Scaffold | 1 AM | 1 h | T-005 | AC-01.1–6 |
| T-007 | RAG | 1 PM | 1 h | T-001 | design §14 |
| T-008 | RAG | 1 PM | 1.5 h | T-007 | AC-08.1 |
| T-009 | RAG | 1 PM | 1 h | T-008 | AC-08.1 |
| T-010 | RAG | 1 PM | 1 h | T-008,9 | AC-08.6 |
| T-011 | RAG | 2 AM | 1.5 h | T-009,10 | AC-08.1,2,5 |
| T-012 ⚠️ | RAG | 2 AM | 1 h | T-011 | AC-09.2,3,5 |
| T-013 | Docs | 2 PM | 1 h | T-001 | AC-03.3,4,8 |
| T-014 | Docs | 2 PM | 1 h | T-013 | AC-03.5,6 |
| T-015 | Docs | 2 PM | 1 h | T-003,4,13,14 | US-03, AC-02 |
| T-016 | Docs | 3 AM | 1.5 h | T-003,15 | AC-04.1–6 |
| T-017 | Docs | 3 AM | 1.5 h | T-007,16 | AC-05.1–7 |
| T-018 | Docs | 3 AM | 1 h | T-016,17 | AC-06.1–5 |
| T-019 ⚠️ | Orch | 3 PM | 1.5 h | T-002,7 | AC-11.1–6 |
| T-020 | Orch | 3 PM | 1.5 h | T-003,4,11,19 | NFR-05,06 |
| T-021 | Orch | 4 AM | 1 h | T-020 | AC-12.1–5 |
| T-022 | Orch | 4 AM | 1 h | T-020 | AC-10.1–4 |
| T-023 | Orch | 4 AM | 1.5 h | T-012,20,21,22 | AC-07,08,09 |
| T-024 | Orch | 4 AM | 1 h | T-023 | AC-13.1–5 |
| T-025 | Orch | 4 PM | 1 h | T-003,4 | AC-14,16 |
| T-026 | Frontend | 4 PM | 1 h | T-005,6 | AC-01.1, AC-02 |
| T-027 | Frontend | 4 PM | 1 h | T-015,26 | AC-03.1,2 |
| T-028 | Frontend | 5 AM | 1.5 h | T-018,27 | AC-05,06 |
| T-029 | Frontend | 5 AM | 1.5 h | T-023,26 | AC-07,09 |
| T-030 | Frontend | 5 AM | 1 h | T-024,25 | AC-13,14 |
| T-031 | Frontend | 5 PM | 1.5 h | T-003 | AC-15.1–5 |
| T-032 | Frontend | 5 PM | 1 h | T-019,26 | AC-11.3, AC-16 |
| T-033 | Voice | 5 PM | 1 h | T-002,3 | AC-12.6 |
| T-034 | Voice | 5 PM | 0.5 h | T-029 | AC-12.7 |
| T-035 | Compare | 6 AM | 2 h | T-016,18 | AC-17 |
| T-036 | Brief | 6 AM | 2 h | T-018,24 | AC-18 |
| T-037 | Eval | 6 PM | 2 h | T-012,19,23 | NFR-12 |
| T-038 | Demo | 7 AM | 1 h | T-023,18 | NFR-07 |
| T-039 | Demo | 7 AM | 1 h | T-001,3 | NFR-02 |
| T-040 | Demo | 7 PM | 2 h | all | all P0 |
| T-041 | Demo | 7 PM | 1.5 h | T-040 | — |

**⚠️ = Critical path task. T-012 (citation validator) and T-019 (safety gate) must be completed and tested before any generation work begins.**
