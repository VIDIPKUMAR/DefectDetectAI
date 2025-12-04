"""
Tests for Kubernetes ML API
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from src.main import app
import numpy as np
import cv2

client = TestClient(app)

def create_test_image():
    """Create a test image with a 'defect'"""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    cv2.circle(img, (50, 50), 10, (0, 0, 255), -1)  # Red circle as "defect"
    return cv2.imencode('.jpg', img)[1].tobytes()

def test_health_endpoint():
    """Test Kubernetes health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_ready_endpoint():
    """Test Kubernetes readiness probe"""
    response = client.get("/ready")
    assert response.status_code in [200, 503]  # 503 if Redis not available

def test_root_endpoint():
    """Test root endpoint with metadata"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "defect-detector"

def test_detect_endpoint():
    """Test defect detection endpoint"""
    test_image = create_test_image()
    
    response = client.post(
        "/detect",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "defects_found" in data
    assert "defect_percentage" in data

@pytest.mark.asyncio
async def test_batch_detect():
    """Test batch processing"""
    test_image = create_test_image()
    
    response = client.post(
        "/batch-detect",
        files=[
            ("files", ("test1.jpg", test_image, "image/jpeg")),
            ("files", ("test2.jpg", test_image, "image/jpeg"))
        ]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_images" in data
    assert data["total_images"] == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])