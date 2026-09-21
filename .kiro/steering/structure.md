# Repo Structure

repo/
  frontend/                 # Next.js app
  backend/
    app/
      api/                  # FastAPI routers
      orchestrator/         # pipeline steps
      rag/                  # ingestion, chunking, retrieval, rerank, citation validator
      documents/            # extraction, OCR, classification, clause analysis, compare
      safety/               # risk gate, emergency resources
      translation/          # translation + glossary
      referrals/            # legal-aid directory + eligibility rules
      models/               # SQLAlchemy + Pydantic schemas
      core/                 # config, auth, logging, security
    data/
      sources/              # curated official PDFs/HTML + manifest.json
      glossary/             # multilingual legal glossary
      legal_aid/            # verified provider dataset
      clause_rules/         # clause risk checklist (YAML/JSON)
    tests/
    scripts/                # ingest_sources.py, build_index.py, evaluate.py
  eval/                     # test docs, Q&A set, metrics report
