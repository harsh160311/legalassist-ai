"""
Document Q&A and clause explanation routes.

Implements interactive legal assistance features:
- Ask questions about uploaded documents (context-aware answers from document content)
- Explain legal clauses in plain language (simplifies complex legal jargon)
- Follow-up question suggestions for deeper understanding
- Helps users prepare information and questions for a legal professional
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    QuestionRequest,
    QuestionResponse,
    ClauseExplainRequest,
    ClauseExplainResponse
)
from ..services.gemini_service import GeminiService
from ..utils.document_store import document_store

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Store GeminiService instance
_ai_service = None


def get_ai_service() -> GeminiService:
    """Get or create GeminiService instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = GeminiService()
    return _ai_service


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about an uploaded document.
    
    The AI will answer based only on the document content.
    """
    # Get document
    document = document_store.get_document(request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.get("extracted_text"):
        raise HTTPException(status_code=400, detail="Document text not extracted")
    
    # Validate question
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Get answer from AI
    try:
        ai_service = get_ai_service()
        answer = ai_service.answer_question(
            question=request.question,
            document_text=document["extracted_text"],
            chat_history=request.chat_history
        )
        
        return QuestionResponse(
            success=True,
            answer=answer,
            asked_at=datetime.now().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")


@router.post("/explain-clause", response_model=ClauseExplainResponse)
async def explain_clause(request: ClauseExplainRequest):
    """
    Explain a specific legal clause in simple language.
    """
    # Validate input
    if not request.clause_text.strip():
        raise HTTPException(status_code=400, detail="Clause text cannot be empty")
    
    # Get document context if provided
    context = request.context or ""
    if request.document_id:
        document = document_store.get_document(request.document_id)
        if document and document.get("extracted_text"):
            # Use first 5000 chars as context
            context = document["extracted_text"][:5000]
    
    # Get explanation from AI
    try:
        ai_service = get_ai_service()
        explanation = ai_service.explain_clause(
            clause_text=request.clause_text,
            document_context=context
        )
        
        return ClauseExplainResponse(
            success=True,
            explanation=explanation,
            explained_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain clause: {str(e)}")
