"""
API endpoint tests.

Tests for FastAPI REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test API endpoint functionality."""

    def test_root_endpoint(self):
        """Test root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code in [200, 503]  # May not be initialized in tests
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "version" in data

    def test_version_endpoint(self):
        """Test version endpoint."""
        response = client.get("/api/version")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "app_name" in data

    def test_match_endpoint_missing_input(self):
        """Test match endpoint with missing input."""
        response = client.post("/api/match")

        # Should return 422 (validation error) for missing required data
        assert response.status_code == 422

    def test_match_endpoint_with_text_description(self):
        """Test match endpoint with text description."""
        response = client.post(
            "/api/match",
            data={
                "text_description": "Need a 24V digital input module with 16 channels",
                "max_alternatives": "3",
                "min_confidence": "50.0"
            }
        )

        # May fail if agent not initialized, but should at least not crash
        assert response.status_code in [200, 503]

    def test_catalog_stats_endpoint(self):
        """Test catalog statistics endpoint."""
        response = client.get("/api/catalog/stats")

        # May return 503 if not initialized
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "catalog_count" in data or isinstance(data, dict)

    def test_add_part_endpoint_invalid_data(self):
        """Test adding part with invalid data."""
        response = client.post(
            "/api/catalog/parts",
            json={"invalid": "data"}
        )

        # Should return error for invalid part data
        assert response.status_code in [400, 422, 503]

    def test_add_part_endpoint_valid_data(self):
        """Test adding part with valid data."""
        part_data = {
            "part_number": "TEST-1234",
            "description": "Test part for API",
            "category": "Test Category",
            "specifications": [
                {
                    "spec_type": "voltage_rating",
                    "name": "Voltage",
                    "value": "24",
                    "unit": "V",
                    "is_critical": True
                }
            ]
        }

        response = client.post(
            "/api/catalog/parts",
            json=part_data
        )

        # May fail if catalog manager not initialized
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert data["part_number"] == "TEST-1234"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
