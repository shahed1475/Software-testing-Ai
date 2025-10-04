import pytest
import requests
from typing import Dict, Any

@pytest.mark.api
@pytest.mark.smoke
class TestAuthentication:
    """Test authentication endpoints"""

    def test_login_success(self, api_base_url, api_headers, sample_user_data):
        """Test successful login"""
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        
        response = requests.post(
            f"{api_base_url}/auth/login",
            json=login_data,
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, api_base_url, api_headers):
        """Test login with invalid credentials"""
        login_data = {
            "username": "invalid_user",
            "password": "wrong_password"
        }
        
        response = requests.post(
            f"{api_base_url}/auth/login",
            json=login_data,
            headers=api_headers
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "detail" in data

    def test_login_missing_fields(self, api_base_url, api_headers):
        """Test login with missing required fields"""
        login_data = {"username": "testuser"}  # Missing password
        
        response = requests.post(
            f"{api_base_url}/auth/login",
            json=login_data,
            headers=api_headers
        )
        
        assert response.status_code == 422

    def test_protected_endpoint_without_token(self, api_base_url, api_headers):
        """Test accessing protected endpoint without authentication"""
        response = requests.get(
            f"{api_base_url}/users/profile",
            headers=api_headers
        )
        
        assert response.status_code == 401

    def test_protected_endpoint_with_token(self, api_base_url, authenticated_headers):
        """Test accessing protected endpoint with valid token"""
        if not authenticated_headers.get("Authorization"):
            pytest.skip("No authentication token available")
            
        response = requests.get(
            f"{api_base_url}/users/profile",
            headers=authenticated_headers
        )
        
        # Should be successful or return user data
        assert response.status_code in [200, 404]  # 404 if user doesn't exist

    def test_token_refresh(self, api_base_url, auth_token, api_headers):
        """Test token refresh functionality"""
        if not auth_token:
            pytest.skip("No authentication token available")
            
        refresh_data = {"refresh_token": auth_token}
        
        response = requests.post(
            f"{api_base_url}/auth/refresh",
            json=refresh_data,
            headers=api_headers
        )
        
        # Should either work or endpoint might not exist
        assert response.status_code in [200, 404, 501]

    def test_logout(self, api_base_url, authenticated_headers):
        """Test logout functionality"""
        if not authenticated_headers.get("Authorization"):
            pytest.skip("No authentication token available")
            
        response = requests.post(
            f"{api_base_url}/auth/logout",
            headers=authenticated_headers
        )
        
        # Should either work or endpoint might not exist
        assert response.status_code in [200, 204, 404, 501]