# NyayaSaathi — Requirements

**Version:** 1.0  
**Scope:** MVP — Residential Tenancy, Tamil Nadu + central baseline, English + Tamil  
**Theme:** AI for Legal Assistance & Access  

---

## Conventions

- **EARS format:** `WHEN <trigger> THE SYSTEM SHALL <behaviour> [SO THAT <rationale>]`
- **Priority:** P0 = demo-blocking MVP | P1 = MVP but not demo-blocking | P2 = should-have
- Every acceptance criterion is deterministically testable (no subjective pass/fail)
- "Standard abstention message" = *"I couldn't verify this information from an authoritative source. Please check the relevant government/legal source or consult a qualified lawyer."*
- "Standard limitation text" = *"NyayaSaathi provides legal information to help you understand and prepare. It is not legal advice and does not replace a qualified lawyer."*

---

## US-01 · Authentication and Anonymous Mode

### User Story
As a first-time user, I want to try the product without creating an account, and optionally sign in with Google to save my work.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-01.1 | WHEN a user opens the app THE SYSTEM SHALL present a language picker (English / Tamil) before any other screen | P0 |
| AC-01.2 | WHEN a user chooses "Try without login" THE SYSTEM SHALL create an anonymous Firebase session and allow full use of document analysis and Q&A | P0 |
| AC-01.3 | WHEN a user signs in with Google via Firebase Auth THE SYSTEM SHALL verify the ID token on the backend using Firebase Admin SDK and scope all data by `user_id` | P0 |
| AC-01.4 | WHEN an anonymous user attempts to save a case THE SYSTEM SHALL prompt them to sign in, preserving their current session state | P1 |
| AC-01.5 | WHEN any API request arrives at the backend THE SYSTEM SHALL reject requests without a valid Firebase ID token with HTTP 401 (anonymous tokens are valid Firebase tokens) | P0 |
| AC-01.6 | WHEN a user signs out THE SYSTEM SHALL clear all in-memory session state and tokens from the browser | P0 |

---

## US-02 · Consent Screen

### User Story
As a user, I want to understand exactly what happens to my document before I upload it, so I can make an informed decision.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-02.1 | WHEN a user initiates a document upload THE SYSTEM SHALL display a consent screen in the user's chosen language before accepting the file | P0 |
| AC-02.2 | WHEN the consent screen is shown THE SYSTEM SHALL clearly state: (a) what data is processed, (b) that PII is masked before any AI call, (c) the auto-delete period, (d) that data is not used for training | P0 |
| AC-02.3 | WHEN a user does not explicitly accept consent THE SYSTEM SHALL not accept the upload or process any document content | P0 |
| AC-02.4 | WHEN consent is accepted THE SYSTEM SHALL record a consent log entry with `user_id`, `timestamp`, `consent_version`, and `language` — never document contents | P0 |
| AC-02.5 | WHEN a user withdraws consent or deletes their account THE SYSTEM SHALL delete all associated documents, analyses, and case data within 24 hours | P1 |

---

## US-03 · Document Upload and Extraction

### User Story
As a renter, I want to upload my rental agreement (PDF, image scan, or DOCX) and have the text extracted accurately, even if the document is a scanned image.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-03.1 | WHEN a user uploads a file THE SYSTEM SHALL accept PDF, JPEG, PNG, and DOCX formats only and reject all others with a clear error message | P0 |
| AC-03.2 | WHEN a file exceeds 10 MB THE SYSTEM SHALL reject it before reading its contents and display the size limit to the user | P0 |
| AC-03.3 | WHEN a PDF is uploaded THE SYSTEM SHALL first attempt PyMuPDF text extraction; if text density is below threshold (< 50 chars/page average) THE SYSTEM SHALL fall back to pytesseract OCR | P0 |
| AC-03.4 | WHEN OCR is used THE SYSTEM SHALL attempt language detection and apply the appropriate Tesseract language pack (eng, tam, or hin) | P0 |
| AC-03.5 | WHEN text is extracted THE SYSTEM SHALL run PII detection (Presidio + Aadhaar/PAN/phone/email regex) and mask all detected PII before passing text to any LLM call | P0 |
| AC-03.6 | WHEN PII is masked THE SYSTEM SHALL never log the unmasked text anywhere in the system | P0 |
| AC-03.7 | WHEN extraction is complete THE SYSTEM SHALL store the masked text with page boundaries, not the original file contents, in the database | P1 |
| AC-03.8 | WHEN a DOCX file is uploaded THE SYSTEM SHALL extract text using python-docx preserving paragraph structure | P0 |

---

## US-04 · Document Classification and Structured Extraction

### User Story
As a renter, I want the system to automatically identify my document as a rental agreement and extract all key facts — parties, rent, deposit, dates, notice periods — into a structured summary.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-04.1 | WHEN a document is extracted THE SYSTEM SHALL classify its type (rental_agreement / other) using the LLM with a Pydantic-validated structured output | P0 |
| AC-04.2 | WHEN classification returns `other` or confidence is low THE SYSTEM SHALL inform the user and offer to proceed with generic analysis | P1 |
| AC-04.3 | WHEN a rental agreement is classified THE SYSTEM SHALL extract a structured record containing: landlord name, tenant name(s), property address, monthly rent, security deposit, lease start date, lease end date, lock-in period, notice period (landlord), notice period (tenant), termination clauses, penalty clauses, maintenance obligations, pet/subletting restrictions, and a clause list with page references | P0 |
| AC-04.4 | WHEN a field cannot be found in the document text THE SYSTEM SHALL set that field to `null` (never invent a value) and flag it as missing in the UI | P0 |
| AC-04.5 | WHEN structured extraction produces a Pydantic validation error THE SYSTEM SHALL retry once; if the second attempt also fails THE SYSTEM SHALL store a partial result and flag the failed fields | P0 |
| AC-04.6 | WHEN deadlines or dates are extracted THE SYSTEM SHALL record the page number and exact quoted clause text as the source for each date | P0 |

---

## US-05 · Clause Risk Analysis

### User Story
As a first-time renter, I want a plain-language breakdown of every clause in my agreement, colour-coded by risk, so I know what to look out for before signing.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-05.1 | WHEN a rental agreement is analysed THE SYSTEM SHALL evaluate every identified clause against the rules in `data/clause_rules/tenancy.yaml` | P0 |
| AC-05.2 | WHEN a clause matches a rule THE SYSTEM SHALL assign a traffic-light rating: `green` (standard), `yellow` (unusual / one-sided), or `red` (high risk / missing critical protection) | P0 |
| AC-05.3 | WHEN generating a plain-language explanation for a flagged clause THE SYSTEM SHALL use the wording "may be unusual or one-sided; consider asking a lawyer" and NEVER use the words "illegal" or "void" unless a retrieved authoritative source directly supports that characterisation | P0 |
| AC-05.4 | WHEN a retrieved source supports a characterisation THE SYSTEM SHALL include a citation card showing source name, section, URL, and `last_verified` date | P0 |
| AC-05.5 | WHEN the following clause patterns are present THE SYSTEM SHALL flag them at minimum yellow/red: asymmetric notice periods, no deposit-refund timeline, landlord entry without notice, unilateral rent hike clause, disproportionate penalty clauses, missing registration/stamp duty mention, missing dispute-resolution clause | P0 |
| AC-05.6 | WHEN the traffic-light is displayed THE SYSTEM SHALL use both colour AND an icon+text label (never colour alone) to meet accessibility requirements | P0 |
| AC-05.7 | WHEN clause analysis is complete THE SYSTEM SHALL display the standard limitation text below the results | P0 |

---

## US-06 · Plain-Language Summary, Glossary, and Lawyer Questions

### User Story
As a renter with no legal background, I want a plain-language summary of my agreement, definitions of confusing terms, and a list of questions I should ask a lawyer.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-06.1 | WHEN document analysis completes THE SYSTEM SHALL produce a plain-language summary of no more than 400 words in the user's chosen language | P0 |
| AC-06.2 | WHEN difficult legal terms appear in the summary or clause analysis THE SYSTEM SHALL hyperlink each to a glossary entry from `data/glossary/legal_terms.json` | P0 |
| AC-06.3 | WHEN the glossary entry is shown THE SYSTEM SHALL display the term in English and the user's chosen language side-by-side | P1 |
| AC-06.4 | WHEN analysis is complete THE SYSTEM SHALL generate 3–7 suggested questions the user could ask a lawyer, grounded in the flagged clauses | P0 |
| AC-06.5 | WHEN generating suggested questions THE SYSTEM SHALL not predict what the answer will be (e.g. do not write "You should ask whether this clause is enforceable because it is not") | P0 |

---

## US-07 · Ask-Your-Document Q&A

### User Story
As a renter, I want to ask free-text questions about my specific agreement and get answers that cite the exact clause and page number.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-07.1 | WHEN a user submits a question in the document Q&A mode THE SYSTEM SHALL restrict its answer to text that appears in the uploaded document | P0 |
| AC-07.2 | WHEN an answer references a document passage THE SYSTEM SHALL include: page number, clause label (if present), and a verbatim quote of the relevant text | P0 |
| AC-07.3 | WHEN the citation validator confirms the quote does not appear verbatim in the cited page THE SYSTEM SHALL regenerate once; if the second attempt also fails THE SYSTEM SHALL respond with the standard abstention message | P0 |
| AC-07.4 | WHEN a question cannot be answered from the document text THE SYSTEM SHALL respond with the standard abstention message and not supplement with general legal information | P0 |
| AC-07.5 | WHEN an answer is displayed THE SYSTEM SHALL label it clearly as "From your document" with the citation | P0 |

---

## US-08 · Legal RAG over Official Sources

### User Story
As a user, I want to ask general tenancy law questions and get answers grounded in official government sources, not the LLM's training data.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-08.1 | WHEN a legal question is asked THE SYSTEM SHALL retrieve relevant chunks from the ChromaDB index using hybrid BM25 + dense search | P0 |
| AC-08.2 | WHEN retrieval runs THE SYSTEM SHALL rerank results with bge-reranker-base and discard chunks below the similarity threshold | P0 |
| AC-08.3 | WHEN a retrieved chunk is used in an answer THE SYSTEM SHALL display a citation card showing: source name, section title, URL, jurisdiction, `effective_date`, and `last_verified` date | P0 |
| AC-08.4 | WHEN no chunk passes the similarity threshold THE SYSTEM SHALL respond with the standard abstention message | P0 |
| AC-08.5 | WHEN a retrieved chunk's jurisdiction does not match the user's stated jurisdiction THE SYSTEM SHALL not use that chunk and ask the user to confirm their state | P0 |
| AC-08.6 | WHEN a source in `manifest.json` has `status: superseded` or `status: repealed` THE SYSTEM SHALL exclude it from retrieval | P0 |
| AC-08.7 | WHEN an answer is generated from official sources THE SYSTEM SHALL label each claim "From official source" with its citation card | P0 |

---

## US-09 · Two-Track Evidence and Citation Validation

### User Story
As a user, I want to know exactly whether each piece of information comes from my document, an official source, or is unverified, so I can trust the answer appropriately.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-09.1 | WHEN a response is generated THE SYSTEM SHALL label every substantive claim as one of: `From your document` (clause citation), `From official source` (source citation), or `General information (unverified)` | P0 |
| AC-09.2 | WHEN the citation validator runs THE SYSTEM SHALL deterministically check: (a) the cited chunk ID exists in the retrieved set for this query, and (b) the quoted text appears verbatim in that chunk | P0 |
| AC-09.3 | WHEN citation validation fails THE SYSTEM SHALL regenerate the response once; if the second validation also fails THE SYSTEM SHALL replace the failed claim with the standard abstention message | P0 |
| AC-09.4 | WHEN an unverified claim is included THE SYSTEM SHALL clearly label it `General information (unverified)` and append the standard abstention message below it | P0 |
| AC-09.5 | WHEN the citation validator runs THE SYSTEM SHALL be implemented as deterministic Python code with no LLM involvement | P0 |

---

## US-10 · Jurisdiction Gate

### User Story
As a user, I want the system to ask me which state I am in before giving jurisdiction-specific advice, rather than guessing and giving me wrong information.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-10.1 | WHEN a user asks a jurisdiction-specific question and no state is recorded in the case THE SYSTEM SHALL ask for the state before answering | P0 |
| AC-10.2 | WHEN the user provides their state THE SYSTEM SHALL store it in the case facts and use it to filter retrieved sources | P0 |
| AC-10.3 | WHEN the extracted document contains a property address THE SYSTEM SHALL pre-fill the jurisdiction but show it to the user for confirmation before using it | P0 |
| AC-10.4 | WHEN THE SYSTEM cannot determine jurisdiction after asking THE SYSTEM SHALL answer using central/baseline sources only and label the response "Central law — may differ in your state" | P0 |

---

## US-11 · Safety / Risk Gate

### User Story
As a user in a high-risk situation, I want the system to recognise that I need urgent help and show me emergency resources immediately, not a legal analysis.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-11.1 | WHEN any user input arrives THE SYSTEM SHALL run the safety gate before any other pipeline step | P0 |
| AC-11.2 | WHEN the safety gate detects keywords/patterns for arrest, criminal allegations, domestic violence, child safety, immediate physical threats, eviction within 24 hours, imminent court deadlines, or self-harm THE SYSTEM SHALL classify the input as high-risk | P0 |
| AC-11.3 | WHEN input is classified as high-risk THE SYSTEM SHALL immediately show: emergency contact numbers (from `data/emergency_contacts.json`), relevant legal-aid pathways, and the standard limitation text — with no strategy, predictions, or legal analysis in the same response | P0 |
| AC-11.4 | WHEN emergency contacts are displayed THE SYSTEM SHALL load them from `data/emergency_contacts.json` (which includes a `verified_at` date) — never from hardcoded strings in prompts or code | P0 |
| AC-11.5 | WHEN the safety gate classification is uncertain THE SYSTEM SHALL use a small LLM classifier (Llama 3.1 8B) to confirm; the LLM decision is advisory but if it returns high-risk the gate activates | P0 |
| AC-11.6 | WHEN high-risk mode activates THE SYSTEM SHALL log the event in the audit log (without document content) and not attempt any downstream pipeline steps | P0 |

---

## US-12 · Multilingual Support (English + Tamil)

### User Story
As a Tamil-speaking user, I want to interact with the system in Tamil and receive responses in Tamil, with legal terms handled correctly.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-12.1 | WHEN a user selects Tamil as their language THE SYSTEM SHALL translate all UI labels, prompts, and generated responses to Tamil | P0 |
| AC-12.2 | WHEN translating output THE SYSTEM SHALL preserve the following untranslated in the target language: statute names, section numbers, monetary amounts, dates, and party names from the document | P0 |
| AC-12.3 | WHEN output is machine-translated THE SYSTEM SHALL display a "Machine translated — may contain errors" label in the target language | P0 |
| AC-12.4 | WHEN a user wants to verify a translation THE SYSTEM SHALL provide a toggle to view the English original alongside the translated output | P0 |
| AC-12.5 | WHEN translating THE SYSTEM SHALL apply a "simple language" pre-pass to replace complex legal English with plain English before translating, using the protected-terms glossary | P1 |
| AC-12.6 | WHEN a user speaks a question via the microphone THE SYSTEM SHALL send the audio to the Groq Whisper endpoint for STT and treat the transcript as the query | P1 |
| AC-12.7 | WHEN an answer is displayed THE SYSTEM SHALL offer a read-aloud button that uses the browser SpeechSynthesis API in the user's chosen language | P1 |
| AC-12.8 | WHEN Hindi is enabled via feature flag THE SYSTEM SHALL apply the same pipeline to Hindi (P2 — add only if time permits) | P2 |

---

## US-13 · Structured Action Plan

### User Story
As a user, I want a clear, structured summary of what I understand, what I can do next, and what documents and deadlines I need to track.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-13.1 | WHEN document analysis and Q&A are complete THE SYSTEM SHALL generate a Structured Action Plan card containing all eight sections: What I understood / Possible legal area / What you can do next / Documents you may need / Important dates / Official resources / When to seek a lawyer / Important limitation | P0 |
| AC-13.2 | WHEN "Important dates" is populated THE SYSTEM SHALL list each date with its source (document page + clause, or official source citation) | P0 |
| AC-13.3 | WHEN "What you can do next" is generated THE SYSTEM SHALL list concrete steps (e.g. "Send a notice in writing") without predicting outcomes | P0 |
| AC-13.4 | WHEN "Important limitation" is populated THE SYSTEM SHALL always include the standard limitation text verbatim | P0 |
| AC-13.5 | WHEN the Action Plan is displayed THE SYSTEM SHALL offer a print/save option | P1 |

---

## US-14 · Case Management

### User Story
As a returning user, I want to save my cases and access my uploaded documents, generated analyses, and deadline list from a dashboard.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-14.1 | WHEN a signed-in user saves a case THE SYSTEM SHALL store: case title, facts (with source enum), linked documents, generated analyses, conversation history, and deadline list | P0 |
| AC-14.2 | WHEN a user opens the case dashboard THE SYSTEM SHALL list all their cases with title, last-updated date, and document count | P0 |
| AC-14.3 | WHEN a deadline is extracted or user-entered THE SYSTEM SHALL add it to the deadline list with its source and display it on the deadlines screen sorted by date | P0 |
| AC-14.4 | WHEN a user deletes a case THE SYSTEM SHALL permanently delete all associated documents, analyses, messages, and deadlines within the same request | P0 |
| AC-14.5 | WHEN the auto-delete period (default 30 days, user-configurable) elapses THE SYSTEM SHALL automatically delete all data for that case and log the deletion in the audit log (without document contents) | P1 |

---

## US-15 · Legal-Aid Finder

### User Story
As a user who cannot afford a lawyer, I want to find free legal aid near me, filtered by state, language, and the type of problem I have.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-15.1 | WHEN a user opens the legal-aid finder THE SYSTEM SHALL display providers from `data/legal_aid/providers.json` filterable by state, district, language, and legal domain | P0 |
| AC-15.2 | WHEN provider results are shown THE SYSTEM SHALL display for each: organisation name, type (DLSA / helpline / NGO), contact details, languages served, and domains covered | P0 |
| AC-15.3 | WHEN a user completes the eligibility quiz THE SYSTEM SHALL apply rule-based criteria (loaded from the providers data file, not scored by AI) to show which providers the user likely qualifies for, with the criteria source | P0 |
| AC-15.4 | WHEN provider results are ranked or ordered THE SYSTEM SHALL use only deterministic rules (alphabetical, distance, domain match) — no AI scoring of lawyers | P0 |
| AC-15.5 | WHEN a provider record is displayed THE SYSTEM SHALL show the `verified_at` date so users know how current the information is | P0 |

---

## US-16 · Privacy Controls

### User Story
As a user, I want full control over my data: I want to know what is stored, set my own auto-delete period, and delete everything at once.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-16.1 | WHEN a user opens privacy settings THE SYSTEM SHALL show: current auto-delete period, consent log (timestamp, version, language), and a delete-all button | P0 |
| AC-16.2 | WHEN a user changes the auto-delete period THE SYSTEM SHALL update it immediately and apply it to all existing and future cases | P0 |
| AC-16.3 | WHEN a user clicks delete-all THE SYSTEM SHALL immediately and permanently delete all their cases, documents, analyses, messages, and deadlines, and add a single deletion entry to the audit log | P0 |
| AC-16.4 | WHEN any system component logs an event THE SYSTEM SHALL never include raw document text, extracted text, or PII in the log entry | P0 |
| AC-16.5 | WHEN the audit log is written THE SYSTEM SHALL record only: `user_id` (hashed), event type, timestamp, and outcome — no content | P0 |

---

## US-17 · Compare Two Documents (P2 — Should-Have)

### User Story
As a renter renewing a lease, I want to upload two versions of an agreement and see exactly what changed, with a plain-language explanation of the impact.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-17.1 | WHEN a user uploads two documents for comparison THE SYSTEM SHALL extract and classify clauses from both documents independently | P2 |
| AC-17.2 | WHEN clause alignment runs THE SYSTEM SHALL use embedding similarity and clause-type labels to match corresponding clauses across documents | P2 |
| AC-17.3 | WHEN comparison is complete THE SYSTEM SHALL output added, removed, and modified clauses with a plain-language description of the impact of each change | P2 |
| AC-17.4 | WHEN a modification is flagged THE SYSTEM SHALL not characterise a change as "better" or "worse" without a grounded source | P2 |

---

## US-18 · Lawyer-Ready Brief PDF (P2 — Should-Have)

### User Story
As a user preparing to consult a lawyer, I want to download a structured PDF summarising my case facts, key clauses, and questions.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-18.1 | WHEN a user requests a brief PDF THE SYSTEM SHALL generate a PDF containing: case facts, extracted structured data, flagged clauses (with citations), action plan, and suggested lawyer questions | P2 |
| AC-18.2 | WHEN the PDF is generated THE SYSTEM SHALL include a cover page with the standard limitation text and the date of generation | P2 |
| AC-18.3 | WHEN the PDF is generated THE SYSTEM SHALL mask any remaining PII that was retained in the structured extraction | P2 |

---

## US-19 · Demand Letter Draft (P2 — Should-Have)

### User Story
As a user wanting to formally request my security deposit back, I want the system to generate a neutral draft demand letter I can edit.

### Acceptance Criteria

| ID | Criterion | Priority |
|----|-----------|----------|
| AC-19.1 | WHEN a user requests a demand letter THE SYSTEM SHALL generate a neutral, factual draft using only information from the case facts and extracted document | P2 |
| AC-19.2 | WHEN the draft is generated THE SYSTEM SHALL refuse any instruction to add abusive, threatening, or fraudulent content | P2 |
| AC-19.3 | WHEN the draft is displayed THE SYSTEM SHALL clearly label it as a draft requiring the user's review and, ideally, a lawyer's review | P2 |

---

## US-20 · Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | All API endpoints must enforce Firebase token verification and scope all queries by `user_id` | P0 |
| NFR-02 | All API endpoints must have per-user rate limiting (chat: 30/min, upload: 10/min) | P0 |
| NFR-03 | All request and response bodies must be validated by Pydantic v2 models | P0 |
| NFR-04 | No secrets, API keys, or model names may appear in source code; all read from env vars | P0 |
| NFR-05 | The orchestrator must use a fixed sequential pipeline of plain Python functions — no autonomous agents | P0 |
| NFR-06 | Each LLM step must produce structured JSON output validated by Pydantic; one retry on validation failure | P0 |
| NFR-07 | Groq API calls must use retry/backoff on rate-limit errors (HTTP 429); demo documents must have a cache layer | P0 |
| NFR-08 | All UI tap targets must be ≥ 48 px; all icons must have text labels (colour is never the only indicator) | P0 |
| NFR-09 | The frontend must be mobile-first (base breakpoint: 375px) and function on a 2G-equivalent connection in low-bandwidth mode | P1 |
| NFR-10 | The system must never fabricate legal content; where verified content is needed and absent, use `TODO_VERIFY` placeholder | P0 |
| NFR-11 | Pytest tests must cover: citation validator (valid + invalid), safety gate (high-risk + safe inputs), clause rules (detection recall), deadline extraction (accuracy), and abstention (unverifiable questions) | P0 |
| NFR-12 | The evaluation harness must measure: citation validity rate, correct abstention rate, clause-detection recall, deadline extraction accuracy, unsafe-output rate on high-risk prompts | P0 |
