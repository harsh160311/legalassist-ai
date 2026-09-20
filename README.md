# LegalAssist AI

**GenAI-Powered Legal Document Analysis & Assistance Platform**

> Making legal information accessible, understandable, and actionable for everyone — regardless of legal expertise or ability to afford a lawyer.

---

## Problem Statement: AI for Legal Assistance & Access

Legal information is complex, full of jargon, and inaccessible to most people. Millions sign contracts, leases, and agreements without understanding the terms, risks, or obligations. Legal consultations cost ₹5,000–₹50,000+ per document review in India, putting professional legal help out of reach for most individuals and small businesses.

**LegalAssist AI solves this by providing instant, AI-powered legal document analysis in plain language — free of cost.**

---

## How Our Solution Maps to Each Use Case

| Problem Statement Use Case | Our Implementation | Where in Code |
|---|---|---|
| **Simplifying complex legal documents** | AI generates plain-language summary + "Summary in Plain Language" section (understandable by a 12-year-old) | `gemini_service.py:_single_stage_analysis`, `gemini_service.py:_two_stage_analysis` |
| **Comparing contracts, agreements, or policies** | Side-by-side document comparison with highlighted similarities, differences, conflicts, and risk levels | `gemini_service.py:compare_documents`, `routes/compare.py` |
| **Highlighting important clauses, obligations, risks, or inconsistencies** | Risk scoring (LOW/MEDIUM/HIGH), obligation extraction with deadlines, clause significance, inconsistency detection | `gemini_service.py` (both stages), `app.js:renderRisks`, `app.js:renderInconsistencies` |
| **Answering questions based on provided legal documents** | Interactive Q&A chatbot with follow-up suggestions, context-aware answers from document content | `gemini_service.py:answer_question`, `routes/chat.py:ask_question` |
| **Helping users understand their options and potential next steps** | "Your Next Steps" summary (high risks, priority actions, missing items), action checklist with interactive checkboxes | `app.js:renderNextStepsSummary`, `app.js:renderActionChecklist` |
| **Generating summaries, checklists, or other actionable outputs** | Document summary, plain-language summary, interactive action checklist (HIGH/MEDIUM/LOW priorities), export (copy/print/download) | `app.js:renderPlainLanguageSummary`, `app.js:renderExportOptions` |
| **Helping users prepare information or questions for a legal professional** | Auto-generated 5+ lawyer questions, clause explainer, print-ready report | `gemini_service.py` (lawyer_questions field), `app.js:renderLawyerQuestions`, `app.js:downloadReport` |

---

## Architecture

```
User Uploads Document (PDF/DOCX/TXT)
        |
Text Extraction (PyPDF2 + AcroForm fields, python-docx)
        |
Adaptive AI Analysis
   |--- Short docs (<8K chars): Single-stage (1 API call, ~30s)
   |--- Long docs (>8K chars): Two-stage pipeline (~40s)
   |       Stage 1: Structured fact extraction (parties, dates, amounts, jurisdiction)
   |       Stage 2: Legal analysis (risks, obligations, inconsistencies, next steps)
        |
Post-Processing
   |--- Sensitive data masking (Aadhaar, PAN, SSN, email, phone)
   |--- Trust indicators (DOCUMENT_FACT / AI_INTERPRETATION / LEGAL_CONCERN)
   |--- Result caching for repeat access
        |
Interactive Features
   |--- Plain language summary + Next Steps summary
   |--- Risk analysis with severity levels
   |--- Inconsistency detection between conflicting clauses
   |--- Action checklist with priorities
   |--- 5+ lawyer preparation questions
   |--- Document Q&A chatbot
   |--- Clause explainer (paste any clause for explanation)
   |--- Side-by-side document comparison
   |--- Export (copy as text, print, download report)
        |
Auto-Cleanup (documents deleted after 10 minutes)
```

---

## Features

### Simplify Legal Documents
- **Plain Language Summary**: AI generates a summary anyone can understand (no legal jargon)
- **Document Overview**: Type, purpose, key parties, and dates extracted
- **Extracted Facts**: Structured data — parties, dates, amounts, addresses, tax IDs, jurisdiction

### Compare Documents
- **Side-by-Side Comparison**: Upload two versions to see exactly what changed
- **Conflict Detection**: Identifies clauses that contradict each other
- **Risk Assessment**: Each difference rated LOW/MEDIUM/HIGH

### Highlight Risks & Clauses
- **Risk Analysis**: Every risk includes explanation, impact, and suggested action
- **Inconsistency Detection**: Flags conflicting clauses across the document
- **Obligation Extraction**: What each party must do, deadlines, and consequences
- **Missing Information**: Flags REQUIRED items that need clarification

### Answer Questions
- **Q&A Chatbot**: Ask any question about the uploaded document
- **Follow-Up Suggestions**: AI suggests deeper questions to explore
- **Clause Explainer**: Paste any legal clause for a plain-language explanation

### Next Steps & Lawyer Prep
- **Action Checklist**: Interactive checklist with HIGH/MEDIUM/LOW priorities
- **Lawyer Questions**: 5+ pre-generated questions for a legal professional
- **Export Report**: Copy as text, print, or download full analysis

### Indian Legal Context
- **Know Your Rights**: Indian Contract Act, Consumer Protection Act, IT Act, RERA
- **Legal Aid Resources**: NALSA, DLSAs, helplines (181, 1800-11-4000, 1930)
- **Sensitive Data**: Auto-masking for Aadhaar, PAN, passport numbers

---

## Security

| Feature | Implementation |
|---|---|
| XSS Prevention | `escapeHtml()` sanitizes all innerHTML injections |
| CORS Lockdown | Restricted to localhost:8000 only |
| Rate Limiting | 30 requests/minute per IP, returns 429 |
| Security Headers | X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy, X-XSS-Protection |
| Prompt Injection Protection | 16 regex patterns detect and block injection attempts |
| Sensitive Data Masking | Auto-masks Aadhaar, PAN, SSN, passport, email, phone |
| Auto-Cleanup | Documents deleted after 10 minutes |
| UNTRUSTED DATA | All AI prompts instruct model to treat documents as untrusted |

---

## Testing

43 automated pytest tests covering:
- Health endpoints, page serving (all 6 pages)
- Document upload, retrieval, text extraction, deletion
- Security headers, CORS validation
- Document comparison, chat endpoints
- Rate limiting, error handling, document lifecycle

```bash
pytest -v
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI (async) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| AI Engine | Google Gemini API (gemini-2.5-flash) |
| PDF Processing | PyPDF2 (text + AcroForm fields) |
| DOCX Processing | python-docx |
| Validation | Pydantic |
| Testing | pytest (43 tests) |

---

## Installation

```bash
git clone https://github.com/harsh160311/legalassist-ai.git
cd legalassist-ai
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Gemini API key
python run.py
```

Open: **http://localhost:8000**

### API Key Setup
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key into your `.env` file as `GEMINI_API_KEY=your_key_here`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/documents/upload | Upload a legal document (PDF/DOCX/TXT) |
| POST | /api/documents/{id}/analyze | Run AI analysis (plain language + risks + next steps) |
| GET | /api/documents/{id} | Get document metadata |
| GET | /api/documents/{id}/text | Get extracted text |
| GET | /api/documents/{id}/analysis | Get stored analysis |
| DELETE | /api/documents/{id} | Delete document |
| POST | /api/chat/ask | Ask a question about a document |
| POST | /api/chat/explain-clause | Explain a clause in plain language |
| POST | /api/compare/ | Compare two documents side-by-side |
| GET | /api/compare/documents | List available documents |
| GET | /api/health | Health check |
| GET | /api/status | API status with config info |

---

## License

MIT License. Created for the Hack2Skill PromptWars hackathon.

## Author

**Harsh Nagpal**
GitHub: https://github.com/harsh160311
