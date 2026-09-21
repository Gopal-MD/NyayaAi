# NyayaAi: Product Steering

NyayaAi is an AI legal-information and document-understanding assistant for India,
built for the hackathon theme "AI for Legal Assistance & Access".

## Non-negotiable principles
1. It provides legal INFORMATION and preparation help. It never gives legal advice,
   predicts case outcomes, or replaces lawyers/courts.
2. Every substantive legal claim must be either:
   (a) grounded in the user's uploaded document (cited by page/clause), or
   (b) grounded in a retrieved official-source chunk (cited with source, section, URL, last_verified).
   Otherwise the system must abstain with the standard abstention message.
3. Citation validation is done by deterministic code, never by the LLM.
4. Deadlines come only from document text, user input, or a curated cited table. Never invented.
5. High-risk situations (arrest, domestic violence, child safety, immediate threats,
   imminent court dates) bypass normal answering and show emergency + legal-aid resources.
6. Legal-aid/lawyer referrals are rule-based and never ranked by AI scores.
7. Privacy first: minimal data, PII masking before LLM calls, auto-delete, no training on user data.

## Standard abstention message
"I couldn't verify this information from an authoritative source. Please check the
relevant government/legal source or consult a qualified lawyer."

## Standard limitation text
"NyayaSaathi provides legal information to help you understand and prepare. It is not
legal advice and does not replace a qualified lawyer."

## MVP scope
Domain: residential tenancy/rental agreements. Jurisdiction: Tamil Nadu + central baseline.
Languages: English, Tamil, Hindi. Everything else is future scope.
