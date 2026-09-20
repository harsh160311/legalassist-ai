"""
Tests for LegalAssist AI backend.
"""

import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["DEBUG"] = "true"
    from backend.main import app
    return TestClient(app)


class TestHealthEndpoints:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data

    def test_api_status(self, client):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data


class TestPageServing:
    def test_dashboard(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_analyze_page(self, client):
        response = client.get("/analyze")
        assert response.status_code == 200

    def test_compare_page(self, client):
        response = client.get("/compare")
        assert response.status_code == 200

    def test_chat_page(self, client):
        response = client.get("/chat")
        assert response.status_code == 200

    def test_legal_info_page(self, client):
        response = client.get("/legal-info")
        assert response.status_code == 200

    def test_about_page(self, client):
        response = client.get("/about")
        assert response.status_code == 200


class TestDocumentUpload:
    def test_upload_txt_file(self, client):
        content = b"This is a test legal document with some terms."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content, "text/plain")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data

    def test_upload_invalid_file_type(self, client):
        content = b"<html>test</html>"
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.exe", content, "application/octet-stream")}
        )
        assert response.status_code == 400


class TestDocumentRetrieval:
    def _upload(self, client):
        content = b"This is a test legal document."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content, "text/plain")}
        )
        return response.json()["document_id"]

    def test_get_document(self, client):
        doc_id = self._upload(client)
        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 200

    def test_get_nonexistent_document(self, client):
        response = client.get("/api/documents/nonexistent")
        assert response.status_code == 404

    def test_delete_document(self, client):
        doc_id = self._upload(client)
        response = client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 404


class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_cors_not_wildcard(self, client):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.headers.get("Access-Control-Allow-Origin") != "*"
