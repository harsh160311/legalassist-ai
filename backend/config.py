import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Application Configuration
APP_NAME = os.getenv("APP_NAME", "LegalAssist AI")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Upload Configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
AUTO_DELETE_MINUTES = int(os.getenv("AUTO_DELETE_MINUTES", "10"))

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
