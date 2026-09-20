"""
Document upload and analysis routes.

Handles the core legal document analysis workflow:
- Upload: Accepts PDF/DOCX/TXT, extracts text (including AcroForm fields)
- Analyze: Two-stage AI pipeline extracts facts + generates legal analysis
  - Simplifies complex legal documents into plain language
  - Highlights important clauses, obligations, risks, and inconsistencies
  - Generates actionable next steps and lawyer preparation questions
- Retrieve: Get document info, extracted text, and stored analysis
- Delete: Remove document and associated files (auto-cleanup after 10 minutes)
"""

import os
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from ..config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from ..models.schemas import DocumentUploadResponse
from ..services.document_extractor import DocumentExtractor
from ..services.gemini_service import GeminiService
from ..utils.document_store import document_store

logger = logging.getLogger("legalassist")

router = APIRouter(prefix="/api/documents", tags=["documents"])

_ai_service = None


def get_ai_service() -> GeminiService:
    global _ai_service
    if _ai_service is None:
        _ai_service = GeminiService()
    return _ai_service


def _write_file(file_path: Path, content: bytes):
    with open(file_path, "wb") as f:
        f.write(content)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        await asyncio.to_thread(_write_file, file_path, content)
    except Exception as e:
        logger.error("Failed to save file: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    document_id = document_store.create_document(
        filename=file.filename,
        file_type=file_ext,
        file_size=len(content),
        file_path=str(file_path)
    )

    logger.info("Upload: id=%s file=%s type=%s size=%d", document_id, file.filename, file_ext, len(content))

    try:
        extraction_result = await asyncio.to_thread(DocumentExtractor.extract_text, str(file_path))
        text_len = len(extraction_result["text"])
        logger.info("Extraction: id=%s text_length=%d pages=%d", document_id, text_len, len(extraction_result["pages"]))

        document_store.update_document(
            document_id,
            extracted_text=extraction_result["text"],
            pages=extraction_result["pages"],
            metadata=extraction_result["metadata"],
            extracted=True
        )
    except Exception as e:
        logger.error("Extraction failed: id=%s error=%s", document_id, e)
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            file_size=len(content),
            file_type=file_ext,
            message=f"Document uploaded but text extraction failed: {str(e)}"
        )

    return DocumentUploadResponse(
        success=True,
        document_id=document_id,
        filename=file.filename,
        file_size=len(content),
        file_type=file_ext,
        message="Document uploaded and text extracted successfully"
    )


@router.post("/{document_id}/analyze")
async def analyze_document(document_id: str):
    document = document_store.get_document(document_id)
    if not document:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": {"type": "NOT_FOUND", "message": "Document not found. It may have been lost due to a server restart. Please upload again."}}
        )

    if not document.get("extracted_text"):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"type": "NO_TEXT", "message": "Document text could not be extracted. The PDF may be scanned/image-based."}}
        )

    text_len = len(document["extracted_text"])
    logger.info("Analyze request: id=%s text_length=%d", document_id, text_len)

    if text_len < 10:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"type": "EMPTY_TEXT", "message": "Extracted text is too short to analyze. The document may be empty or image-based."}}
        )

    try:
        ai_service = get_ai_service()
    except Exception as e:
        logger.error("AI service init failed: %s", e)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"type": "AI_CONFIG_ERROR", "message": f"Gemini API is not configured correctly: {str(e)}"}}
        )

    try:
        analysis = ai_service.analyze_document(
            document_text=document["extracted_text"],
            document_metadata=document.get("metadata")
        )
    except Exception as e:
        logger.error("AI analyze exception: %s", e)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"type": "AI_EXCEPTION", "message": f"AI analysis crashed: {str(e)}"}}
        )

    if isinstance(analysis, dict) and "error" in analysis:
        logger.error("AI returned error: %s", analysis["error"])
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"type": "AI_ANALYSIS_ERROR", "message": analysis["error"]}}
        )

    document_store.update_document(
        document_id,
        analysis=analysis,
        analyzed_at=datetime.now().isoformat()
    )

    logger.info("Analysis complete: id=%s type=%s", document_id, analysis.get("document_type", "unknown"))

    return {
        "success": True,
        "document_id": document_id,
        "analysis": analysis,
        "analyzed_at": datetime.now().isoformat()
    }


@router.get("/{document_id}")
async def get_document(document_id: str):
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document["document_id"],
        "filename": document["filename"],
        "file_type": document["file_type"],
        "file_size": document["file_size"],
        "uploaded_at": document["uploaded_at"],
        "extracted": document.get("extracted", False),
        "analyzed": document.get("analysis") is not None,
        "page_count": len(document.get("pages", []))
    }


@router.get("/{document_id}/text")
async def get_document_text(document_id: str):
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.get("extracted_text"):
        raise HTTPException(status_code=400, detail="Text not extracted")

    return {
        "document_id": document_id,
        "text": document["extracted_text"],
        "pages": document.get("pages", []),
        "metadata": document.get("metadata", {})
    }


@router.get("/{document_id}/analysis")
async def get_document_analysis(document_id: str):
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.get("analysis"):
        raise HTTPException(status_code=400, detail="Document not analyzed yet")

    return {
        "document_id": document_id,
        "analysis": document["analysis"],
        "analyzed_at": document.get("analyzed_at")
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    document = document_store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = document.get("file_path")
    if file_path and os.path.exists(file_path):
        await asyncio.to_thread(os.remove, file_path)

    document_store.delete_document(document_id)
    return {"success": True, "message": "Document deleted"}
