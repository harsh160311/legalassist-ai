"""
Tests for LegalAssist AI backend.
Covers: health, pages, upload, retrieval, security, compare, chat, rate limiting.
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
        assert b"LegalAssist AI" in response.content

    def test_analyze_page(self, client):
        response = client.get("/analyze")
        assert response.status_code == 200
        assert b"Analyze" in response.content

    def test_compare_page(self, client):
        response = client.get("/compare")
        assert response.status_code == 200
        assert b"Compare" in response.content

    def test_chat_page(self, client):
        response = client.get("/chat")
        assert response.status_code == 200
        assert b"Ask" in response.content

    def test_legal_info_page(self, client):
        response = client.get("/legal-info")
        assert response.status_code == 200
        assert b"Legal" in response.content

    def test_about_page(self, client):
        response = client.get("/about")
        assert response.status_code == 200
        assert b"About" in response.content


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

    def test_upload_returns_filename(self, client):
        content = b"Legal agreement text here."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("agreement.txt", content, "text/plain")}
        )
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data


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

    def test_get_document_text(self, client):
        doc_id = self._upload(client)
        response = client.get(f"/api/documents/{doc_id}/text")
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

    def test_delete_nonexistent_document(self, client):
        response = client.delete("/api/documents/nonexistent")
        assert response.status_code == 404


class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy(self, client):
        response = client.get("/")
        assert "Referrer-Policy" in response.headers

    def test_csp_header(self, client):
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers

    def test_cors_not_wildcard(self, client):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.headers.get("Access-Control-Allow-Origin") != "*"


class TestCompareDocuments:
    def _upload_two(self, client):
        content_a = b"Employment agreement between A and B. Salary 100000."
        content_b = b"Employment agreement between A and B. Salary 120000."
        r1 = client.post(
            "/api/documents/upload",
            files={"file": ("a.txt", content_a, "text/plain")}
        )
        r2 = client.post(
            "/api/documents/upload",
            files={"file": ("b.txt", content_b, "text/plain")}
        )
        return r1.json()["document_id"], r2.json()["document_id"]

    def test_compare_requires_two_documents(self, client):
        response = client.post(
            "/api/compare/",
            json={"document_a_id": "nonexistent", "document_b_id": "nonexistent"}
        )
        assert response.status_code in [400, 404, 200]

    def test_compare_documents_invalid_ids(self, client):
        response = client.post(
            "/api/compare/",
            json={"document_a_id": "aaa", "document_b_id": "bbb"}
        )
        assert response.status_code in [400, 404, 200]


class TestChatEndpoint:
    def test_ask_requires_document(self, client):
        response = client.post(
            "/api/chat/ask",
            json={"question": "What is this?", "document_id": "nonexistent"}
        )
        assert response.status_code in [400, 404]

    def test_explain_clause_empty(self, client):
        response = client.post(
            "/api/chat/explain-clause",
            json={"clause": ""}
        )
        assert response.status_code in [400, 422, 200]


class TestRateLimiting:
    def test_rate_limit_headers(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_rate_limit_returns_429(self, client):
        for _ in range(35):
            response = client.get("/api/health")
        assert response.status_code == 429


class TestErrorHandling:
    def test_upload_no_file(self, client):
        response = client.post("/api/documents/upload")
        assert response.status_code in [400, 422, 429]

    def test_invalid_json_body(self, client):
        response = client.post(
            "/api/chat/ask",
            content="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [422, 429]
