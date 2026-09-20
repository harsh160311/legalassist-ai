# LegalAssist AI

**AI-Powered Legal Document Analysis & Assistance Platform**

---

## Overview

LegalAssist AI is a full-stack web application that uses Google Gemini AI to help users understand, analyze, and compare legal documents. It extracts key facts, identifies risks, and provides actionable insights — making legal information accessible to everyone.

> **Note:** This platform provides information and assistance, not professional legal advice.

---

## Features

| Feature | Description |
|---|---|
| Two-Stage AI Analysis | Stage 1 extracts facts, Stage 2 generates legal analysis |
| Document Type Detection | Automatically identifies contracts, tax forms, NDAs, etc. |
| Sensitive Data Masking | Auto-detects and masks Aadhaar, PAN, SSN, passport, tax IDs |
| Fact vs Inference | Clearly separates document facts from AI interpretations |
| Document Q&A | Ask questions, get answers from document content only |
| Clause Explanation | Paste any clause for plain-language explanation |
| Document Comparison | Compare two documents for changes, additions, removals |
| PDF Form Field Extraction | Extracts fillable form field values (AcroForm) |
| Prompt Injection Protection | Detects and blocks injection attempts |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| AI Engine | Google Gemini API (`gemini-1.5-flash`) |
| PDF Processing | PyPDF2 (text + AcroForm fields) |
| DOCX Processing | python-docx |
| Environment | python-dotenv |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A Google Gemini API key (free to generate)

### Generate Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated key

> **Important:** Never share your API key publicly or commit it to version control.

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd legalassist-ai

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
```

### Configure Your API Key

Open `.env` and replace the placeholder with your actual Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

### Run the Application

```bash
python run.py
```

Open your browser and navigate to: **http://localhost:8000**

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key | **Required** |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `APP_NAME` | Application name | `LegalAssist AI` |
| `APP_VERSION` | Application version | `1.0.0` |
| `DEBUG` | Enable debug mode | `true` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `MAX_FILE_SIZE_MB` | Max upload size | `10` |
| `AUTO_DELETE_MINUTES` | Auto-delete uploaded files | `10` |

---

## Project Structure

```
legalassist-ai/
├── backend/
│   ├── main.py                    # FastAPI application, routing, static files
│   ├── config.py                  # Environment configuration
│   ├── routes/
│   │   ├── documents.py           # Document upload, analysis, retrieval
│   │   ├── chat.py                # Q&A and clause explanation
│   │   └── compare.py             # Document comparison
│   ├── services/
│   │   ├── document_extractor.py  # PDF/DOCX/TXT + AcroForm extraction
│   │   └── gemini_service.py      # Two-stage AI analysis + safety
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   └── utils/
│       └── document_store.py      # In-memory document storage
├── frontend/
│   ├── index.html                 # Dashboard
│   ├── analyze.html               # Upload & analyze documents
│   ├── compare.html               # Compare two documents
│   ├── chat.html                  # Ask questions about documents
│   ├── legal-info.html            # General legal information
│   ├── about.html                 # About page + disclaimer
│   ├── css/
│   │   └── styles.css             # Professional legal design system
│   └── js/
│       └── app.js                 # Frontend logic, rendering, state
├── uploads/                       # Uploaded document storage
├── .env.example                   # Environment template
├── .gitignore
├── requirements.txt               # Python dependencies
├── run.py                         # Application entry point
└── README.md
```

---

## AI Analysis Pipeline

```
Upload Document
      │
      ▼
┌─────────────────────┐
│  Text Extraction     │  PyPDF2 + AcroForm fields
│  (PDF/DOCX/TXT)     │  → Merges labels + form values
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  STAGE 1:            │  Gemini API call
│  Fact Extraction     │  → identification_details
│                     │  → tax_identifiers
│                     │  → treaty_information
│                     │  → amounts, dates, addresses
│                     │  → jurisdiction
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  STAGE 2:            │  Gemini API call
│  Legal Analysis      │  Uses extracted facts + original text
│                     │  → summary, parties, clauses
│                     │  → risks, missing_information
│                     │  → action_checklist
│                     │  → lawyer_questions
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Post-Processing     │  Sensitive data masking
│                     │  JSON validation
│                     │  Trust indicator injection
└─────────┬───────────┘
          │
          ▼
    Frontend Render
```

---

## API Endpoints

### Documents
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/documents/upload` | Upload a document (PDF/DOCX/TXT) |
| POST | `/api/documents/{id}/analyze` | Run two-stage AI analysis |
| GET | `/api/documents/{id}` | Get document info |
| GET | `/api/documents/{id}/text` | Get extracted text |
| GET | `/api/documents/{id}/analysis` | Get stored analysis |
| DELETE | `/api/documents/{id}` | Delete a document |

### Chat
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat/ask` | Ask a question about a document |
| POST | `/api/chat/explain-clause` | Explain a legal clause |

### Compare
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/compare/` | Compare two documents |
| GET | `/api/compare/documents` | List available documents |

### System
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/status` | API status with config info |

---

## Safety Features

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` with restricted sources

### CORS
- Locked to `localhost:8000` and `127.0.0.1:8000` only
- Only `GET`, `POST`, `DELETE` methods allowed
- Only `Content-Type` header accepted

### Rate Limiting
- 30 requests per minute per IP
- Returns `429 Too Many Requests` when exceeded

### XSS Prevention
- All dynamic content escaped with `escapeHtml()` before DOM insertion
- User input and API responses sanitized

### Prompt Injection Protection

The system detects and blocks:
- "Ignore previous instructions"
- "Reveal system prompt" / "Reveal API key"
- "You are now..." / "New instructions:"
- Jailbreak and override attempts

### Data Handling

- Documents treated as **UNTRUSTED DATA**
- API key never exposed to frontend
- Sensitive identifiers masked in UI
- No full sensitive data in logs
- Documents auto-deleted after 10 minutes

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test class
pytest tests/test_app.py::TestHealthEndpoints -v
```

### Test Coverage
- Health and status endpoints
- Page serving (all 6 pages)
- Document upload (valid + invalid types)
- Document retrieval and deletion
- Security headers verification
- CORS configuration validation

---

## Accessibility

- Skip-to-content link for keyboard navigation
- ARIA landmarks (`role="main"`, `role="contentinfo"`, `aria-label`)
- Keyboard-navigable mobile toggle and interactive elements
- `prefers-reduced-motion` support
- Focus-visible indicators
- Semantic HTML structure
- Responsive design with mobile breakpoints

---

## Supported Document Types

- Contracts and Agreements
- Employment Agreements
- Rental/Lease Agreements
- Non-Disclosure Agreements (NDA)
- Tax Forms (W-8BEN, W-9, etc.)
- Terms of Service / Privacy Policies
- Digital Signature Records
- Government Forms
- Any PDF, DOCX, or TXT file

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `GEMINI_API_KEY` not set | Make sure `.env` file exists with your API key |
| Port 8000 in use | Change `PORT` in `.env` to another value |
| Upload fails | Check `MAX_FILE_SIZE_MB` in `.env` |
| Module not found | Ensure virtual environment is activated |
| AI analysis fails | Verify your Gemini API key is valid at [AI Studio](https://makersuite.google.com/app/apikey) |

---

## License

MIT License. Created for the Hack2Skill PromptWars hackathon.

---

## Author

**Harsh Nagpal**
GitHub: https://github.com/harsh160311
