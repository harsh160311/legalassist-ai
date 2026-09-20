"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    success: bool
    document_id: str
    filename: str
    file_size: int
    file_type: str
    message: str


class AnalysisRequest(BaseModel):
    """Request to analyze a document."""
    document_id: str


class AnalysisResponse(BaseModel):
    """Response containing document analysis."""
    success: bool
    document_id: str
    analysis: Dict[str, Any]
    analyzed_at: str


class QuestionRequest(BaseModel):
    """Request to ask a question about a document."""
    document_id: str
    question: str
    chat_history: Optional[List[Dict[str, str]]] = []


class QuestionResponse(BaseModel):
    """Response to a document question."""
    success: bool
    answer: Dict[str, Any]
    asked_at: str


class ClauseExplainRequest(BaseModel):
    """Request to explain a clause."""
    clause_text: str
    document_id: Optional[str] = None
    context: Optional[str] = ""


class ClauseExplainResponse(BaseModel):
    """Response with clause explanation."""
    success: bool
    explanation: Dict[str, Any]
    explained_at: str


class CompareRequest(BaseModel):
    """Request to compare two documents."""
    document_a_id: str
    document_b_id: str


class CompareResponse(BaseModel):
    """Response with document comparison."""
    success: bool
    comparison: Dict[str, Any]
    compared_at: str


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: str
    page_count: Optional[int] = None
    extracted: bool = False
    analyzed: bool = False
