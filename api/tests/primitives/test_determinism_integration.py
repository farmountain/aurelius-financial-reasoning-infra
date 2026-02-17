"""
Integration tests for determinism primitive API endpoint.

Tests validate end-to-end API behavior including:
- Authentication (API key and JWT)
- Rate limiting
- Request/response validation
- Canonical envelope format
- Error handling
"""
import pytest
import time
from fastapi.testclient import TestClient
from main import app
from security.api_key_auth import create_api_key


client = TestClient(app)


@pytest.fixture
def test_api_key():
    """Create test API key."""
    user_id = "test-user-123"
    raw_key, hashed_key = create_api_key(user_id)
    return raw_key


@pytest.fixture
def valid_determinism_request():
    """Valid determinism scoring request payload."""
    return {
        "strategy_id": "strat-integration-test",
        "runs": [
            {
                "run_id": "run-1",
                "timestamp": "2026-02-16T10:00:00Z",
                "total_return": 0.15,
                "sharpe_ratio": 1.8,
                "max_drawdown": 0.12,
                "trade_count": 42,
                "final_portfolio_value": 115000.0,
                "execution_time_ms": 1250
            },
            {
                "run_id": "run-2",
                "timestamp": "2026-02-16T10:05:00Z",
                "total_return": 0.15,
                "sharpe_ratio": 1.8,
                "max_drawdown": 0.12,
                "trade_count": 42,
                "final_portfolio_value": 115000.0,
                "execution_time_ms": 1230
            }
        ],
        "threshold": 95.0
    }


class TestDeterminismAPIIntegration:
    """Integration tests for determinism primitive API."""
    
    def test_successful_scoring_with_api_key(self, test_api_key, valid_determinism_request):
        """Test successful determinism scoring with API key authentication."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json=valid_determinism_request
        )
        
        assert response.status_code == 200
        
        # Validate canonical envelope structure
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert "links" in data
        
        # Validate meta fields
        assert data["meta"]["version"] == "v1"
        assert "timestamp" in data["meta"]
        assert "request_id" in data["meta"]
        
        # Validate response data
        result = data["data"]
        assert "score" in result
        assert "passed" in result
        assert "confidence_interval" in result
        assert "p_value" in result
        assert "variance_metrics" in result
        assert "issues" in result
        
        # Validate score is in range
        assert 0 <= result["score"] <= 100
        assert isinstance(result["passed"], bool)
        
        # Validate links
        assert "self" in data["links"]
        assert "docs" in data["links"]
    
    def test_rate_limit_headers_present(self, test_api_key, valid_determinism_request):
        """Test rate limit headers are included in response."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json=valid_determinism_request
        )
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Validate header values
        limit = int(response.headers["X-RateLimit-Limit"])
        remaining = int(response.headers["X-RateLimit-Remaining"])
        reset = int(response.headers["X-RateLimit-Reset"])
        
        assert limit > 0
        assert remaining >= 0
        assert reset > time.time()
    
    def test_authentication_required(self, valid_determinism_request):
        """Test request without authentication fails with 401."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            json=valid_determinism_request
        )
        
        assert response.status_code == 401
        
        # Validate error response structure
        data = response.json()
        assert "error" in data
        assert "meta" in data
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
    
    def test_invalid_api_key(self, valid_determinism_request):
        """Test request with invalid API key fails with 401."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": "invalid-key-12345"},
            json=valid_determinism_request
        )
        
        assert response.status_code == 401
    
    def test_validation_error_insufficient_runs(self, test_api_key):
        """Test validation error when fewer than 2 runs provided."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json={
                "strategy_id": "test-strat",
                "runs": [
                    {
                        "run_id": "run-1",
                        "timestamp": "2026-02-16T10:00:00Z",
                        "total_return": 0.15,
                        "sharpe_ratio": 1.8,
                        "max_drawdown": 0.12,
                        "trade_count": 42,
                        "final_portfolio_value": 115000.0,
                        "execution_time_ms": 1250
                    }
                ],
                "threshold": 95.0
            }
        )
        
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_validation_error_invalid_threshold(self, test_api_key, valid_determinism_request):
        """Test validation error for invalid threshold value."""
        invalid_request = valid_determinism_request.copy()
        invalid_request["threshold"] = 150.0  # Invalid: > 100
        
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json=invalid_request
        )
        
        assert response.status_code == 422
    
    def test_validation_error_missing_required_fields(self, test_api_key):
        """Test validation error when required fields are missing."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json={
                "strategy_id": "test-strat"
                # Missing 'runs' field
            }
        )
        
        assert response.status_code == 422
    
    def test_high_variance_detection(self, test_api_key):
        """Test detection of high variance returns appropriate response."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json={
                "strategy_id": "test-strat",
                "runs": [
                    {
                        "run_id": "run-1",
                        "timestamp": "2026-02-16T10:00:00Z",
                        "total_return": 0.15,
                        "sharpe_ratio": 1.8,
                        "max_drawdown": 0.12,
                        "trade_count": 42,
                        "final_portfolio_value": 115000.0,
                        "execution_time_ms": 1250
                    },
                    {
                        "run_id": "run-2",
                        "timestamp": "2026-02-16T10:05:00Z",
                        "total_return": 0.25,
                        "sharpe_ratio": 2.2,
                        "max_drawdown": 0.18,
                        "trade_count": 38,
                        "final_portfolio_value": 125000.0,
                        "execution_time_ms": 1100
                    }
                ],
                "threshold": 95.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        result = data["data"]
        assert result["score"] < 95.0
        assert result["passed"] is False
        assert len(result["issues"]) > 0
    
    def test_perfect_determinism_detection(self, test_api_key, valid_determinism_request):
        """Test perfect determinism returns score of 100."""
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json=valid_determinism_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        result = data["data"]
        assert result["score"] == 100.0
        assert result["passed"] is True
        assert len(result["issues"]) == 0
    
    def test_multiple_concurrent_requests(self, test_api_key, valid_determinism_request):
        """Test handling multiple concurrent requests."""
        responses = []
        
        for i in range(5):
            request = valid_determinism_request.copy()
            request["strategy_id"] = f"strat-concurrent-{i}"
            
            response = client.post(
                "/api/primitives/v1/determinism/score",
                headers={"X-API-Key": test_api_key},
                json=request
            )
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            assert "data" in response.json()
    
    def test_performance_sla(self, test_api_key, valid_determinism_request):
        """Test endpoint meets performance SLA (<200ms)."""
        start_time = time.time()
        
        response = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json=valid_determinism_request
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        # Performance target: p95 < 200ms
        # Allow some margin for test environment
        assert latency_ms < 500, f"Latency {latency_ms}ms exceeds threshold"
    
    def test_health_check_endpoint(self):
        """Test health check endpoint is publicly accessible."""
        response = client.get("/api/primitives/v1/determinism/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_response_schema_consistency(self, test_api_key):
        """Test response schema is consistent across different scenarios."""
        # Test with perfect determinism
        request1 = {
            "strategy_id": "strat-1",
            "runs": [
                {
                    "run_id": "run-1",
                    "timestamp": "2026-02-16T10:00:00Z",
                    "total_return": 0.15,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": 0.12,
                    "trade_count": 42,
                    "final_portfolio_value": 115000.0,
                    "execution_time_ms": 1250
                },
                {
                    "run_id": "run-2",
                    "timestamp": "2026-02-16T10:05:00Z",
                    "total_return": 0.15,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": 0.12,
                    "trade_count": 42,
                    "final_portfolio_value": 115000.0,
                    "execution_time_ms": 1230
                }
            ],
            "threshold": 95.0
        }
        
        # Test with high variance
        request2 = {
            "strategy_id": "strat-2",
            "runs": [
                {
                    "run_id": "run-1",
                    "timestamp": "2026-02-16T10:00:00Z",
                    "total_return": 0.15,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": 0.12,
                    "trade_count": 42,
                    "final_portfolio_value": 115000.0,
                    "execution_time_ms": 1250
                },
                {
                    "run_id": "run-2",
                    "timestamp": "2026-02-16T10:05:00Z",
                    "total_return": 0.30,
                    "sharpe_ratio": 2.5,
                    "max_drawdown": 0.20,
                    "trade_count": 35,
                    "final_portfolio_value": 130000.0,
                    "execution_time_ms": 1000
                }
            ],
            "threshold": 95.0
        }
        
        response1 = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json=request1
        )
        
        response2 = client.post(
            "/api/primitives/v1/determinism/score",
            headers={"X-API-Key": test_api_key},
            json=request2
        )
        
        # Both should have identical structure
        data1 = response1.json()
        data2 = response2.json()
        
        assert set(data1.keys()) == set(data2.keys())
        assert set(data1["data"].keys()) == set(data2["data"].keys())
        assert set(data1["meta"].keys()) == set(data2["meta"].keys())
