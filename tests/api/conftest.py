import pytest
import requests
import json
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API testing"""
    return os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

@pytest.fixture(scope="session")
def api_headers():
    """Default headers for API requests"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "TestingAI/1.0"
    }

@pytest.fixture(scope="session")
def auth_token(api_base_url, api_headers):
    """Authentication token for protected endpoints"""
    auth_data = {
        "username": os.getenv("TEST_USERNAME", "testuser"),
        "password": os.getenv("TEST_PASSWORD", "testpass")
    }
    
    response = requests.post(
        f"{api_base_url}/auth/login",
        json=auth_data,
        headers=api_headers
    )
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

@pytest.fixture
def authenticated_headers(api_headers, auth_token):
    """Headers with authentication token"""
    headers = api_headers.copy()
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    return headers

@pytest.fixture
def api_client(api_base_url, api_headers):
    """API client session"""
    session = requests.Session()
    session.headers.update(api_headers)
    session.base_url = api_base_url
    return session

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePass123!"
    }

@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "name": "Test Product",
        "description": "A test product for API testing",
        "price": 99.99,
        "category": "electronics",
        "in_stock": True
    }

@pytest.fixture(autouse=True)
def test_metadata(request):
    """Automatically capture test metadata"""
    test_name = request.node.name
    test_file = request.node.fspath.basename
    
    # Store metadata for reporting
    request.node.test_metadata = {
        "test_name": test_name,
        "test_file": test_file,
        "markers": [marker.name for marker in request.node.iter_markers()]
    }

def pytest_runtest_makereport(item, call):
    """Hook to capture test results for reporting"""
    if call.when == "call":
        # Store test result for custom reporting
        item.test_result = {
            "outcome": call.excinfo is None,
            "duration": call.duration,
            "metadata": getattr(item, 'test_metadata', {})
        }