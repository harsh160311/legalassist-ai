# LegalAssist AI

**AI-Powered Legal Document Analysis & Assistance Platform**

> Making legal information accessible, understandable, and actionable for everyone — regardless of legal expertise.

---

## Chosen Vertical

**AI for Legal Assistance & Access**

Legal documents are complex, difficult to understand, and challenging to navigate without professional assistance. LegalAssist AI is a GenAI-powered solution that makes legal information and basic legal assistance more accessible by helping users understand, compare, and navigate legal documents.

### Problem We Solve

Most people sign contracts, leases, and agreements without fully understanding the terms, risks, or obligations. Legal services are expensive and inaccessible for many. LegalAssist AI bridges this gap by providing instant, AI-powered analysis that breaks down complex legal language into plain English.

### Target Users

- Individuals reviewing contracts or agreements
- Small business owners without legal teams
- Students learning about legal documents
- Anyone who needs to understand legal documents quickly
- People who cannot afford expensive legal consultations

---

## How Our Solution Maps to Use Cases

| Problem Statement Use Case | Our Implementation |
|---|---|
| **Simplifying complex legal documents** | Two-stage AI pipeline extracts facts + generates plain-English summary, risk analysis, and obligation breakdown |
| **Comparing contracts, agreements, or policies** | Side-by-side document comparison with highlighted similarities, differences, and conflicts |
| **Highlighting important clauses, obligations, risks, or inconsistencies** | Risk scoring (LOW/MEDIUM/HIGH), obligation extraction with deadlines, clause-by-clause significance analysis |
| **Answering questions based on provided legal documents** | Interactive Q&A chatbot — ask any question about uploaded documents, get context-aware answers |
| **Helping users understand their options and potential next steps** | Action checklist with priorities (HIGH/MEDIUM/LOW), "Questions to Ask a Lawyer" section, next-steps guidance |
| **Generating summaries, checklists, or other actionable outputs** | Document summary, interactive action checklist, lawyer preparation questions, financial/termination/liability summaries |
| **Helping users prepare information or questions for a legal professional** | Auto-generated lawyer questions based on document analysis, printable checklist, clause explanations |

---

## Approach and Logic

The platform follows a structured approach to legal document analysis:

```
User Uploads Document (PDF/DOCX/TXT)
        |
Text Extraction (including AcroForm fields)
        |
Single-Stage or Two-Stage AI Analysis
   |--- Short docs: Single-stage (1 API call, ~30s)
   |--- Long docs: Stage 1 (Fact Extraction) → Stage 2 (Legal Analysis)
        |
Post-Processing (sensitive data masking, trust indicators)
        |
Frontend Rendering (interactive dashboard with next steps)
        |
Interactive Follow-up (Q&A chatbot, clause explanations, document comparison)
```

### Core Logic

1. **Document Ingestion** — Accept PDF, DOCX, or TXT files. Extract text including fillable form fields (AcroForm).

2. **Adaptive AI Pipeline** — Short documents (<8000 chars) use single-stage analysis (1 API call, faster). Longer documents use two-stage pipeline:
   - **Stage 1 (Fact Extraction):** Extract structured facts — parties, dates, amounts, addresses, tax identifiers, jurisdiction. Clean, verifiable data.
   - **Stage 2 (Legal Analysis):** Generate risks, obligations, missing information, action checklist, and questions for a lawyer.

3. **Safety Layer** — Prompt injection protection, sensitive data masking (Aadhaar, PAN, SSN), trust indicators, and UNTRUSTED DATA treatment.

4. **Interactive Features** — Ask follow-up questions, explain individual clauses, compare multiple documents side-by-side.

---

## How the Solution Works

### Step 1: User Uploads a Document
Users drag-and-drop or click to upload a legal document (PDF, DOCX, or TXT). The system validates file type and size (max 10MB).

### Step 2: Text Extraction
- **PDF:** PyPDF2 extracts text + AcroForm field values (filled-in form data)
- **DOCX:** python-docx extracts paragraph text
- **TXT:** Direct text read with encoding fallback

### Step 3: AI Analysis
**For short documents** — Single API call extracts facts and generates analysis simultaneously. Faster (~30 seconds).

**For long documents** — Two-stage pipeline:
- **Stage 1:** Extracts parties, dates, amounts, addresses, tax IDs, jurisdiction, clauses
- **Stage 2:** Generates summary, risks (with severity levels), obligations (with deadlines), missing info, action checklist, and lawyer preparation questions

### Step 4: Post-Processing
- Sensitive data (Aadhaar, PAN, SSN) automatically masked
- Trust indicators injected (document fact vs. AI interpretation)
- Results cached for repeat access

### Step 5: Interactive Features
- **Document Q&A:** Ask any question about the uploaded document
- **Clause Explanation:** Paste any clause for plain-language explanation
- **Document Comparison:** Compare two documents side-by-side
- **Action Checklist:** Interactive checklist with priorities you can track
- **Lawyer Questions:** Pre-generated questions to ask a legal professional

### Step 6: Auto-Cleanup
Uploaded documents are automatically deleted after 10 minutes — no permanent storage, no privacy risk.

---

## Assumptions Made

1. **Readable documents** — The system assumes uploaded PDFs have extractable text (not scanned images).
2. **API key available** — Requires a Google Gemini API key (free from Google AI Studio).
3. **Internet required** — AI analysis needs an active internet connection.
4. **English-optimized** — Analysis is optimized for English legal documents.
5. **Informational only** — Results are for informational purposes, not legal advice.
6. **Ephemeral storage** — Documents auto-deleted after 10 minutes.
7. **MVP scope** — No user authentication in this version.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| AI Engine | Google Gemini API (gemini-2.5-flash) |
| PDF Processing | PyPDF2 (text + AcroForm fields) |
| DOCX Processing | python-docx |
| Validation | Pydantic |
| Testing | pytest |

---

## Evaluation Focus Areas

### High Impact — Code Quality, Security, Testing

| Area | Implementation |
|---|---|
| **Modular Architecture** | Backend split into routes/, services/, models/, utils/ |
| **Python Typing** | Pydantic models for all request/response schemas |
| **XSS Prevention** | `escapeHtml()` sanitizes all innerHTML injections |
| **CORS Lockdown** | Restricted to localhost:8000 (was wildcard `*`) |
| **Rate Limiting** | 30 requests/min per IP, returns 429 |
| **Security Headers** | X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy |
| **Prompt Injection Protection** | 16 regex patterns detect and block injection attempts |
| **Sensitive Data Masking** | Auto-masks Aadhaar, PAN, SSN, passport, email, phone |
| **Auto-Cleanup** | Documents deleted after 10 minutes |
| **15 pytest tests** | Health, pages, upload, retrieval, security headers, CORS |

### Medium Impact — Efficiency, Problem Alignment

| Area | Implementation |
|---|---|
| **Adaptive Pipeline** | Short docs: 1 API call (~30s). Long docs: 2 calls (~40s) |
| **Async FastAPI** | All route handlers are async def |
| **Async File I/O** | Sync file operations wrapped in asyncio.to_thread |
| **Document Truncation** | Limits text sent to AI (60K chars max) |
| **Background Cleanup** | Non-blocking asyncio task for expired documents |
| **Result Caching** | Same document analyzed instantly on repeat access |
| **Two-Stage Pipeline** | Separates fact extraction from legal analysis for accuracy |
| **Trust Indicators** | Every claim classified as DOCUMENT_FACT, AI_INTERPRETATION, or LEGAL_CONCERN |

### Low Impact — Accessibility, Documentation

| Area | Implementation |
|---|---|
| **Skip-to-content link** | Keyboard users skip navigation |
| **ARIA landmarks** | role="main", role="contentinfo", aria-label on nav |
| **Keyboard navigation** | Nav toggle, checklist items, suggested questions |
| **prefers-reduced-motion** | Animations disabled when user prefers |
| **Focus-visible indicators** | Clear outline on keyboard focus |
| **Responsive design** | Mobile-first with breakpoints at 600px, 768px, 900px |
| **Comprehensive README** | Vertical, approach, evaluation alignment, troubleshooting |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/documents/upload | Upload a document (PDF/DOCX/TXT) |
| POST | /api/documents/{id}/analyze | Run AI analysis |
| GET | /api/documents/{id} | Get document info |
| GET | /api/documents/{id}/text | Get extracted text |
| GET | /api/documents/{id}/analysis | Get stored analysis |
| DELETE | /api/documents/{id} | Delete a document |
| POST | /api/chat/ask | Ask a question about a document |
| POST | /api/chat/explain-clause | Explain a legal clause |
| POST | /api/compare/ | Compare two documents |
| GET | /api/compare/documents | List available documents |
| GET | /api/health | Health check |
| GET | /api/status | API status with config info |

---

## Installation

```bash
git clone https://github.com/harsh160311/legalassist-ai.git
cd legalassist-ai
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Gemini API key
python run.py
```

Open: **http://localhost:8000**

### Get Your API Key
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key into your `.env` file

---

## License

MIT License. Created for the Hack2Skill PromptWars hackathon.

## Author

**Harsh**
GitHub: https://github.com/harsh160311
