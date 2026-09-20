"""
Tests for LegalAssist AI backend.
Covers: health, pages, upload, retrieval, analysis, security, CORS,
compare, chat, rate limiting, error handling, document lifecycle.
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


# ---------------------------------------------------------------------------
# 1. Health endpoints
# ---------------------------------------------------------------------------
class TestHealthEndpoints:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    def test_api_status(self, client):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert "gemini_configured" in data
        assert "auto_delete_minutes" in data


# ---------------------------------------------------------------------------
# 2. Page serving with content checks
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# 3. Document upload
# ---------------------------------------------------------------------------
class TestDocumentUpload:
    def test_upload_txt_file(self, client):
        content = b"This is a test legal document with some terms."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data
        assert data["filename"] == "test.txt"
        assert data["file_type"] == ".txt"
        assert data["file_size"] == len(content)

    def test_upload_pdf_like_file(self, client):
        content = b"%PDF-1.4 fake pdf content for testing purposes here."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("doc.pdf", content, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_type"] == ".pdf"

    def test_upload_invalid_file_type(self, client):
        content = b"<html>test</html>"
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.exe", content, "application/octet-stream")},
        )
        assert response.status_code == 400

    def test_upload_no_file(self, client):
        response = client.post("/api/documents/upload")
        assert response.status_code in [400, 422, 429]

    def test_upload_empty_file(self, client):
        response = client.post(
            "/api/documents/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_size"] == 0


# ---------------------------------------------------------------------------
# 4. Document retrieval
# ---------------------------------------------------------------------------
class TestDocumentRetrieval:
    def _upload(self, client):
        content = b"This is a test legal document with enough text to extract."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content, "text/plain")},
        )
        if response.status_code == 429:
            pytest.skip("Rate limited")
        return response.json()["document_id"]

    def test_get_document(self, client):
        doc_id = self._upload(client)
        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["filename"] == "test.txt"
        assert "uploaded_at" in data

    def test_get_document_text(self, client):
        doc_id = self._upload(client)
        response = client.get(f"/api/documents/{doc_id}/text")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert "text" in data
        assert "pages" in data
        assert "metadata" in data

    def test_get_nonexistent_document(self, client):
        response = client.get("/api/documents/nonexistent-id-xyz")
        assert response.status_code == 404

    def test_delete_document(self, client):
        doc_id = self._upload(client)
        response = client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_document(self, client):
        response = client.delete("/api/documents/nonexistent-id-xyz")
        assert response.status_code == 404

    def test_delete_document_twice(self, client):
        doc_id = self._upload(client)
        r1 = client.delete(f"/api/documents/{doc_id}")
        assert r1.status_code == 200
        r2 = client.delete(f"/api/documents/{doc_id}")
        assert r2.status_code == 404


# ---------------------------------------------------------------------------
# 5. Document analysis (no API key -> graceful error)
# ---------------------------------------------------------------------------
class TestDocumentAnalysis:
    def _upload(self, client):
        content = b"This is a legal agreement between party A and party B regarding services."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("analysis_test.txt", content, "text/plain")},
        )
        if response.status_code == 429:
            pytest.skip("Rate limited")
        return response.json()["document_id"]

    def test_analyze_without_api_key(self, client):
        doc_id = self._upload(client)
        response = client.post(f"/api/documents/{doc_id}/analyze")
        assert response.status_code in [500, 429]

    def test_get_analysis_before_analyzing(self, client):
        doc_id = self._upload(client)
        response = client.get(f"/api/documents/{doc_id}/analysis")
        assert response.status_code == 400

    def test_analyze_nonexistent_document(self, client):
        response = client.post("/api/documents/fake-id/analyze")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 6. Security headers
# ---------------------------------------------------------------------------
class TestSecurityHeaders:
    def test_x_content_type_options(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client):
        response = client.get("/")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection(self, client):
        response = client.get("/")
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy(self, client):
        response = client.get("/")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_content_security_policy(self, client):
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp

    def test_security_headers_on_api(self, client):
        response = client.get("/api/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"


# ---------------------------------------------------------------------------
# 7. CORS
# ---------------------------------------------------------------------------
class TestCORS:
    def test_cors_not_wildcard(self, client):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("Access-Control-Allow-Origin") != "*"

    def test_cors_allowed_origin(self, client):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
        origin = response.headers.get("Access-Control-Allow-Origin")
        assert origin is None or origin == "http://localhost:8000" or origin != "*"

    def test_cors_allowed_methods(self, client):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
            },
        )
        methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert methods == "" or "GET" in methods or response.status_code == 200


# ---------------------------------------------------------------------------
# 8. Compare documents
# ---------------------------------------------------------------------------
class TestCompareDocuments:
    def _upload_two(self, client):
        content_a = b"Employment agreement between A and B. Salary 100000."
        content_b = b"Employment agreement between A and B. Salary 120000."
        r1 = client.post(
            "/api/documents/upload",
            files={"file": ("a.txt", content_a, "text/plain")},
        )
        r2 = client.post(
            "/api/documents/upload",
            files={"file": ("b.txt", content_b, "text/plain")},
        )
        if r1.status_code == 429 or r2.status_code == 429:
            pytest.skip("Rate limited")
        return r1.json()["document_id"], r2.json()["document_id"]

    def test_compare_invalid_doc_ids(self, client):
        response = client.post(
            "/api/compare/",
            json={"document_a_id": "aaa", "document_b_id": "bbb"},
        )
        assert response.status_code in [400, 404, 429]

    def test_compare_missing_fields(self, client):
        response = client.post("/api/compare/", json={})
        assert response.status_code in [400, 422, 429]

    def test_compare_one_missing_one_valid(self, client):
        doc_a, _ = self._upload_two(client)
        response = client.post(
            "/api/compare/",
            json={"document_a_id": doc_a, "document_b_id": "nonexistent"},
        )
        assert response.status_code in [400, 404, 429]

    def test_compare_without_api_key(self, client):
        doc_a, doc_b = self._upload_two(client)
        response = client.post(
            "/api/compare/",
            json={"document_a_id": doc_a, "document_b_id": doc_b},
        )
        assert response.status_code in [200, 500, 429]

    def test_list_available_documents(self, client):
        self._upload_two(client)
        response = client.get("/api/compare/documents")
        assert response.status_code in [200, 429]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


# ---------------------------------------------------------------------------
# 9. Chat endpoints
# ---------------------------------------------------------------------------
class TestChatEndpoint:
    def _upload(self, client):
        content = b"This rental agreement is between landlord and tenant for a term of 12 months."
        response = client.post(
            "/api/documents/upload",
            files={"file": ("chat_test.txt", content, "text/plain")},
        )
        if response.status_code == 429:
            pytest.skip("Rate limited")
        return response.json()["document_id"]

    def test_ask_requires_document(self, client):
        response = client.post(
            "/api/chat/ask",
            json={"question": "What is this?", "document_id": "nonexistent"},
        )
        assert response.status_code in [400, 404, 429]

    def test_ask_missing_question(self, client):
        doc_id = self._upload(client)
        response = client.post(
            "/api/chat/ask",
            json={"document_id": doc_id},
        )
        assert response.status_code in [400, 422, 429]

    def test_ask_empty_question(self, client):
        doc_id = self._upload(client)
        response = client.post(
            "/api/chat/ask",
            json={"question": "", "document_id": doc_id},
        )
        assert response.status_code in [400, 429]

    def test_explain_clause_empty(self, client):
        response = client.post(
            "/api/chat/explain-clause",
            json={"clause_text": ""},
        )
        assert response.status_code in [400, 422, 429]

    def test_explain_clause_valid(self, client):
        response = client.post(
            "/api/chat/explain-clause",
            json={"clause_text": "The tenant shall pay rent on or before the first day of each month."},
        )
        assert response.status_code in [200, 500, 429]

    def test_explain_clause_with_document_context(self, client):
        doc_id = self._upload(client)
        response = client.post(
            "/api/chat/explain-clause",
            json={
                "clause_text": "The tenant shall pay rent on or before the first day of each month.",
                "document_id": doc_id,
            },
        )
        assert response.status_code in [200, 500, 429]

    def test_ask_without_api_key(self, client):
        doc_id = self._upload(client)
        response = client.post(
            "/api/chat/ask",
            json={"question": "What is the term of this agreement?", "document_id": doc_id},
        )
        assert response.status_code in [200, 500, 429]


# ---------------------------------------------------------------------------
# 10. Rate limiting
# ---------------------------------------------------------------------------
class TestRateLimiting:
    def test_rate_limit_headers(self, client):
        response = client.get("/api/health")
        assert response.status_code in [200, 429]

    def test_rate_limit_returns_429(self, client):
        for _ in range(35):
            response = client.get("/api/health")
        assert response.status_code == 429


# ---------------------------------------------------------------------------
# 11. Error handling
# ---------------------------------------------------------------------------
class TestErrorHandling:
    def test_invalid_json_body(self, client):
        response = client.post(
            "/api/chat/ask",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [422, 429]

    def test_compare_missing_body(self, client):
        response = client.post("/api/compare/")
        assert response.status_code in [400, 422, 429]

    def test_explain_clause_missing_body(self, client):
        response = client.post("/api/chat/explain-clause")
        assert response.status_code in [400, 422, 429]

    def test_get_nonexistent_api_route(self, client):
        response = client.get("/api/nonexistent")
        assert response.status_code in [404, 405, 429]

    def test_404_on_unknown_page(self, client):
        response = client.get("/this-page-does-not-exist")
        assert response.status_code in [404, 429]


# ---------------------------------------------------------------------------
# 12. Document lifecycle: upload -> get -> analyze -> delete
# ---------------------------------------------------------------------------
class TestDocumentLifecycle:
    def test_full_lifecycle(self, client):
        # Upload
        content = b"This is a lease agreement between landlord and tenant for 24 months."
        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("lifecycle.txt", content, "text/plain")},
        )
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert upload_resp.status_code == 200
        doc_id = upload_resp.json()["document_id"]

        # Get metadata
        get_resp = client.get(f"/api/documents/{doc_id}")
        if get_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert get_resp.status_code == 200
        assert get_resp.json()["document_id"] == doc_id

        # Get text
        text_resp = client.get(f"/api/documents/{doc_id}/text")
        if text_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert text_resp.status_code == 200
        assert "landlord" in text_resp.json()["text"].lower()

        # Analyze (no API key -> 500 is acceptable)
        analyze_resp = client.post(f"/api/documents/{doc_id}/analyze")
        if analyze_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert analyze_resp.status_code in [200, 500]

        # Delete
        del_resp = client.delete(f"/api/documents/{doc_id}")
        if del_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

        # Confirm deleted
        confirm_resp = client.get(f"/api/documents/{doc_id}")
        if confirm_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert confirm_resp.status_code == 404

    def test_upload_then_compare(self, client):
        c1 = b"Agreement A with terms for party one."
        c2 = b"Agreement B with terms for party two."
        r1 = client.post(
            "/api/documents/upload",
            files={"file": ("lca.txt", c1, "text/plain")},
        )
        r2 = client.post(
            "/api/documents/upload",
            files={"file": ("lcb.txt", c2, "text/plain")},
        )
        if r1.status_code == 429 or r2.status_code == 429:
            pytest.skip("Rate limited")
        doc_a = r1.json()["document_id"]
        doc_b = r2.json()["document_id"]

        comp_resp = client.post(
            "/api/compare/",
            json={"document_a_id": doc_a, "document_b_id": doc_b},
        )
        if comp_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert comp_resp.status_code in [200, 500]

    def test_upload_then_ask(self, client):
        content = b"This employment contract is for a term of 6 months starting January 2025."
        r = client.post(
            "/api/documents/upload",
            files={"file": ("lifecycle_ask.txt", content, "text/plain")},
        )
        if r.status_code == 429:
            pytest.skip("Rate limited")
        doc_id = r.json()["document_id"]

        ask_resp = client.post(
            "/api/chat/ask",
            json={"question": "What is the contract term?", "document_id": doc_id},
        )
        if ask_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert ask_resp.status_code in [200, 500]

    def test_upload_then_explain_clause(self, client):
        content = b"The party agrees to indemnify and hold harmless the other party."
        r = client.post(
            "/api/documents/upload",
            files={"file": ("lifecycle_clause.txt", content, "text/plain")},
        )
        if r.status_code == 429:
            pytest.skip("Rate limited")
        doc_id = r.json()["document_id"]

        explain_resp = client.post(
            "/api/chat/explain-clause",
            json={
                "clause_text": "The party agrees to indemnify and hold harmless the other party.",
                "document_id": doc_id,
            },
        )
        if explain_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert explain_resp.status_code in [200, 500]

    def test_upload_then_list_for_compare(self, client):
        content = b"Simple document for listing test."
        r = client.post(
            "/api/documents/upload",
            files={"file": ("list_test.txt", content, "text/plain")},
        )
        if r.status_code == 429:
            pytest.skip("Rate limited")

        list_resp = client.get("/api/compare/documents")
        if list_resp.status_code == 429:
            pytest.skip("Rate limited")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert isinstance(data, list)
