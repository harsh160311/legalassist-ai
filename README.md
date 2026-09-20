# LegalAssist AI

**AI-Powered Legal Document Analysis & Assistance Platform**

---

## Chosen Vertical

**AI for Legal Assistance & Access**

LegalAssist AI is built under the **Legal Assistance & Access** vertical. The platform focuses on making legal information accessible, understandable, and actionable for everyone - regardless of legal expertise.

### Target Users

- Individuals reviewing contracts or agreements
- Small business owners without legal teams
- Students learning about legal documents
- Anyone who needs to understand legal documents quickly

### Problem We Solve

Legal documents are complex, full of jargon, and often misunderstood. Most people sign contracts without fully understanding the terms, risks, or obligations. LegalAssist AI bridges this gap by providing instant, AI-powered analysis that breaks down complex legal language into plain English.

---

## Approach and Logic

The platform follows a structured approach to legal document analysis:

```
User Uploads Document
        |
Text Extraction (PDF/DOCX/TXT + AcroForm fields)
        |
Two-Stage AI Analysis
   |--- Stage 1: Fact Extraction (structured data)
   |--- Stage 2: Legal Analysis (risks, obligations, recommendations)
        |
Post-Processing (sensitive data masking, trust indicators)
        |
Frontend Rendering (interactive dashboard)
```

### Core Logic

1. **Document Ingestion** - Accept PDF, DOCX, or TXT files. Extract text including fillable form fields (AcroForm).

2. **Two-Stage AI Pipeline** - Instead of asking AI to do everything at once, we split the work:
   - **Stage 1 (Fact Extraction):** Extract structured facts - parties, dates, amounts, addresses, tax identifiers, jurisdiction. This gives us clean, verifiable data.
   - **Stage 2 (Legal Analysis):** Use the extracted facts + original text to generate legal analysis - summary, risks, obligations, missing information, action checklist, and questions for a lawyer.

3. **Safety Layer** - Apply prompt injection protection, sensitive data masking, and trust indicators to ensure responsible AI usage.

4. **Interactive Features** - Enable users to ask follow-up questions, explain individual clauses, and compare multiple documents.

---

## How the Solution Works

### Step 1: User Uploads a Document

Users drag-and-drop or click to upload a legal document (PDF, DOCX, or TXT). The system validates file type and size (max 10MB).

### Step 2: Text Extraction

The backend extracts text from the document:
- **PDF:** PyPDF2 extracts text + AcroForm field values (filled-in form data)
- **DOCX:** python-docx extracts paragraph text
- **TXT:** Direct text read with encoding fallback

### Step 3: Two-Stage AI Analysis

**Stage 1 - Fact Extraction:**

The AI extracts structured facts from the document:
- Identification details (parties, document type)
- Tax identifiers (PAN, Aadhaar, SSN, etc.)
- Financial amounts and payment terms
- Key dates and deadlines
- Addresses and jurisdiction
- Treaty information (for international documents)

**Stage 2 - Legal Analysis:**

Using the extracted facts, the AI generates:
- Document summary and type classification
- Involved parties and their obligations
- Important clauses with significance
- Potential concerns and risks (with severity levels)
- Missing/unclear information
- Action checklist with priorities
- Questions to ask a lawyer

### Step 4: Post-Processing

Before displaying results:
- Sensitive data (Aadhaar, PAN, SSN, etc.) is masked
- Trust indicators are injected (document fact vs. AI interpretation)
- JSON response is validated and cleaned

### Step 5: Interactive Features

- **Document Q&A:** Ask any question about the uploaded document
- **Clause Explanation:** Paste any clause for plain-language explanation
- **Document Comparison:** Compare two documents side-by-side

### Step 6: Auto-Cleanup

Uploaded documents are automatically deleted after 10 minutes - no permanent storage, no privacy risk.

---

## Assumptions Made

1. **User-provided documents are in readable format** - The system assumes uploaded PDFs have extractable text (not scanned images).

2. **API key is available** - The system requires a Google Gemini API key. Users can generate one for free from Google AI Studio.

3. **Internet access required** - AI analysis requires an active internet connection to reach the Gemini API.

4. **English-language documents** - The AI analysis is optimized for English legal documents. Other languages may produce less accurate results.

5. **Awareness, not certification** - Analysis results are for informational purposes only and do not constitute legal advice or certified legal opinions.

6. **Ephemeral storage** - Documents are stored in-memory and auto-deleted after 10 minutes. Server restarts clear all data.

7. **Single-user MVP** - This is an MVP version without user authentication. All uploaded documents are accessible to anyone with the URL during the session.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| AI Engine | Google Gemini API (gemini-1.5-flash) |
| PDF Processing | PyPDF2 (text + AcroForm fields) |
| DOCX Processing | python-docx |
| Validation | Pydantic |
| Environment | python-dotenv |
| Testing | pytest |

---

## Evaluation Focus Areas

### Code Quality

| Implementation | Details |
|---|---|
| Modular Architecture | Backend split into routes/, services/, models/, utils/ |
| Python Typing | Pydantic models for all request/response schemas |
| Separation of Concerns | Routes delegate to services, services handle business logic |
| Configuration | Externalized to .env + config.py |
| Docstrings | Present on all classes, methods, and route handlers |
| Logging | Structured logging with named logger across all modules |

### Security

| Implementation | Details |
|---|---|
| XSS Prevention | `escapeHtml()` function sanitizes all innerHTML injections |
| CORS Lockdown | Restricted to localhost:8000 only (was wildcard) |
| Rate Limiting | 30 requests per minute per IP, returns 429 |
| Security Headers | X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy |
| Prompt Injection Protection | 16 regex patterns detect and block injection attempts |
| Sensitive Data Masking | Auto-masks Aadhaar, PAN, SSN, passport, email, phone |
| API Key Security | Loaded from .env, never exposed to frontend |
| File Validation | Server-side extension whitelist + size limit |
| Auto-Cleanup | Documents deleted after 10 minutes |
| UNTRUSTED DATA | All AI prompts instruct model to treat documents as untrusted |

### Efficiency

| Implementation | Details |
|---|---|
| Async FastAPI | All route handlers are async def |
| Async File I/O | Sync file operations wrapped in asyncio.to_thread |
| Document Truncation | Limits text sent to AI (100K chars max) |
| Background Cleanup | Non-blocking asyncio task for expired documents |
| Lazy AI Init | GeminiService created on first use (singleton pattern) |
| No-Cache Headers | Fresh content on every page load |
| JSON Robust Parsing | Handles markdown fences, common escape issues |

### Testing

| Implementation | Details |
|---|---|
| 15 pytest tests | All passing |
| Health endpoints | Health check, API status |
| Page serving | All 6 frontend pages |
| Document upload | Valid files, invalid type rejection |
| Document retrieval | Get, delete, 404 handling |
| Security headers | Verify all headers present |
| CORS validation | Verify wildcard is not used |

Run tests:
```bash
pytest -v
```

### Accessibility

| Implementation | Details |
|---|---|
| Skip-to-content link | Keyboard users can skip navigation |
| ARIA landmarks | role="main", role="contentinfo", aria-label on nav |
| Keyboard navigation | Nav toggle, checklist items, suggested questions |
| prefers-reduced-motion | Animations disabled when user prefers |
| Focus-visible indicators | Clear outline on keyboard focus |
| Semantic HTML | Proper heading hierarchy, nav, main, footer |
| Responsive design | Mobile-first with breakpoints at 600px, 768px, 900px |
| Form labels | Associated labels on all form inputs |

---

## How the Work is Evaluated

### High Impact (Most Important)

| Criteria | Our Implementation |
|---|---|
| **Code Quality** | Modular FastAPI backend with clean separation of services, routes, models, utils. Pydantic validation. Structured logging. |
| **Security** | XSS sanitization, CORS lockdown, rate limiting, prompt injection protection, sensitive data masking, CSP headers, auto-cleanup. |
| **Testing** | 15 automated pytest tests covering health, pages, uploads, retrieval, security headers, and CORS. |

### Medium Impact (Under the Surface)

| Criteria | Our Implementation |
|---|---|
| **Efficiency** | Async handlers, asyncio.to_thread for sync I/O, document truncation, background cleanup, lazy initialization. |
| **Problem Alignment** | Two-stage AI pipeline for accurate legal analysis. Fact extraction + legal analysis separation. Trust indicators. |

### Low Impact (Final Polish)

| Criteria | Our Implementation |
|---|---|
| **Accessibility** | Skip links, ARIA landmarks, keyboard navigation, prefers-reduced-motion, focus-visible, responsive design. |
| **Documentation** | Comprehensive README with vertical, approach, evaluation alignment, troubleshooting. |

---

## API Endpoints

### Documents

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/documents/upload | Upload a document (PDF/DOCX/TXT) |
| POST | /api/documents/{id}/analyze | Run two-stage AI analysis |
| GET | /api/documents/{id} | Get document info |
| GET | /api/documents/{id}/text | Get extracted text |
| GET | /api/documents/{id}/analysis | Get stored analysis |
| DELETE | /api/documents/{id} | Delete a document |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/chat/ask | Ask a question about a document |
| POST | /api/chat/explain-clause | Explain a legal clause |

### Compare

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/compare/ | Compare two documents |
| GET | /api/compare/documents | List available documents |

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/health | Health check |
| GET | /api/status | API status with config info |

---

## Installation

```bash
# Clone repository
git clone https://github.com/harsh160311/legalassist-ai.git
cd legalassist-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your Gemini API key

# Run
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

---

## Author

**Harsh Nagpal**
GitHub: https://github.com/harsh160311
