"""
Simple in-memory storage for document metadata.
In production, use a database.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import uuid
import os
import logging

logger = logging.getLogger("legalassist")

# Auto-delete after 10 minutes (imported from config)
from ..config import AUTO_DELETE_MINUTES


class DocumentStore:
    """In-memory storage for document information."""
    
    def __init__(self):
        self._documents: Dict[str, dict] = {}
    
    def create_document(self, filename: str, file_type: str, file_size: int, file_path: str) -> str:
        """Create a new document record and return document_id."""
        document_id = str(uuid.uuid4())
        
        self._documents[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "file_path": file_path,
            "uploaded_at": datetime.now().isoformat(),
            "extracted_text": None,
            "extracted": False,
            "pages": None,
            "metadata": None,
            "analysis": None,
            "analyzed_at": None
        }
        
        return document_id
    
    def get_document(self, document_id: str) -> Optional[dict]:
        """Get document by ID."""
        return self._documents.get(document_id)
    
    def update_document(self, document_id: str, **kwargs) -> bool:
        """Update document fields."""
        if document_id not in self._documents:
            return False
        
        for key, value in kwargs.items():
            self._documents[document_id][key] = value
        
        return True
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        if document_id in self._documents:
            doc = self._documents[document_id]
            file_path = doc.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info("Deleted file: %s", file_path)
                except Exception as e:
                    logger.error("Failed to delete file %s: %s", file_path, e)
            del self._documents[document_id]
            return True
        return False
    
    def list_documents(self) -> List[dict]:
        """List all documents."""
        return list(self._documents.values())
    
    def document_exists(self, document_id: str) -> bool:
        """Check if document exists."""
        return document_id in self._documents
    
    def cleanup_expired_documents(self) -> int:
        """Delete documents older than AUTO_DELETE_MINUTES. Returns count of deleted docs."""
        expired_ids = []
        cutoff_time = datetime.now() - timedelta(minutes=AUTO_DELETE_MINUTES)
        
        for doc_id, doc in self._documents.items():
            try:
                uploaded_at = datetime.fromisoformat(doc["uploaded_at"])
                if uploaded_at < cutoff_time:
                    expired_ids.append(doc_id)
            except (ValueError, KeyError):
                continue
        
        for doc_id in expired_ids:
            self.delete_document(doc_id)
            logger.info("Auto-deleted expired document: %s", doc_id)
        
        if expired_ids:
            logger.info("Cleaned up %d expired documents", len(expired_ids))
        
        return len(expired_ids)


# Global instance
document_store = DocumentStore()
