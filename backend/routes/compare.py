"""
Document comparison routes.

Compares two legal documents side-by-side:
- Identifies key differences in clauses, terms, and obligations
- Highlights added/removed clauses between versions
- Compares payment terms, termination conditions, liability, and jurisdiction
- Generates risk-level assessments for each difference
- Helps users understand contract changes before signing
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from ..models.schemas import CompareRequest, CompareResponse
from ..services.gemini_service import GeminiService
from ..utils.document_store import document_store

router = APIRouter(prefix="/api/compare", tags=["compare"])

# Store GeminiService instance
_ai_service = None


def get_ai_service() -> GeminiService:
    """Get or create GeminiService instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = GeminiService()
    return _ai_service


@router.post("/", response_model=CompareResponse)
async def compare_documents(request: CompareRequest):
    """
    Compare two legal documents.
    
    Returns detailed comparison of terms, clauses, and changes.
    """
    # Get Document A
    doc_a = document_store.get_document(request.document_a_id)
    if not doc_a:
        raise HTTPException(status_code=404, detail="Document A not found")
    
    if not doc_a.get("extracted_text"):
        raise HTTPException(status_code=400, detail="Document A text not extracted")
    
    # Get Document B
    doc_b = document_store.get_document(request.document_b_id)
    if not doc_b:
        raise HTTPException(status_code=404, detail="Document B not found")
    
    if not doc_b.get("extracted_text"):
        raise HTTPException(status_code=400, detail="Document B text not extracted")
    
    # Compare with AI
    try:
        ai_service = get_ai_service()
        comparison = ai_service.compare_documents(
            document_a_text=doc_a["extracted_text"],
            document_b_text=doc_b["extracted_text"]
        )
        
        return CompareResponse(
            success=True,
            comparison=comparison,
            compared_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/documents")
async def list_available_documents():
    """List all uploaded documents available for comparison."""
    documents = document_store.list_documents()
    
    return [
        {
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "file_type": doc["file_type"],
            "uploaded_at": doc["uploaded_at"],
            "extracted": doc.get("extracted", False)
        }
        for doc in documents
        if doc.get("extracted", False)
    ]
