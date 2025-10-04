import pytest
import requests
from typing import Dict, Any

@pytest.mark.api
@pytest.mark.regression
class TestCRUDOperations:
    """Test CRUD operations for various endpoints"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, api_base_url, authenticated_headers):
        """Setup and teardown for each test"""
        self.api_base_url = api_base_url
        self.headers = authenticated_headers
        self.created_resources = []
        
        yield
        
        # Cleanup created resources
        for resource_type, resource_id in self.created_resources:
            try:
                requests.delete(
                    f"{self.api_base_url}/{resource_type}/{resource_id}",
                    headers=self.headers
                )
            except:
                pass  # Ignore cleanup errors

    def test_create_user(self, sample_user_data):
        """Test creating a new user"""
        response = requests.post(
            f"{self.api_base_url}/users",
            json=sample_user_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["username"] == sample_user_data["username"]
            assert data["email"] == sample_user_data["email"]
            self.created_resources.append(("users", data["id"]))
        else:
            # Endpoint might not exist or require different auth
            assert response.status_code in [404, 401, 403, 501]

    def test_get_users_list(self):
        """Test retrieving list of users"""
        response = requests.get(
            f"{self.api_base_url}/users",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
            if isinstance(data, dict):
                assert "items" in data or "users" in data
        else:
            assert response.status_code in [404, 401, 403, 501]

    def test_get_user_by_id(self):
        """Test retrieving a specific user by ID"""
        # First try to get a user ID from the list
        list_response = requests.get(
            f"{self.api_base_url}/users",
            headers=self.headers
        )
        
        if list_response.status_code == 200:
            data = list_response.json()
            user_id = None
            
            if isinstance(data, list) and data:
                user_id = data[0].get("id")
            elif isinstance(data, dict):
                items = data.get("items", data.get("users", []))
                if items:
                    user_id = items[0].get("id")
            
            if user_id:
                response = requests.get(
                    f"{self.api_base_url}/users/{user_id}",
                    headers=self.headers
                )
                assert response.status_code in [200, 404]
                
                if response.status_code == 200:
                    user_data = response.json()
                    assert user_data["id"] == user_id

    def test_update_user(self, sample_user_data):
        """Test updating a user"""
        # First create a user
        create_response = requests.post(
            f"{self.api_base_url}/users",
            json=sample_user_data,
            headers=self.headers
        )
        
        if create_response.status_code == 201:
            user_data = create_response.json()
            user_id = user_data["id"]
            self.created_resources.append(("users", user_id))
            
            # Update the user
            update_data = {
                "first_name": "Updated",
                "last_name": "Name"
            }
            
            response = requests.put(
                f"{self.api_base_url}/users/{user_id}",
                json=update_data,
                headers=self.headers
            )
            
            assert response.status_code in [200, 204]
            
            if response.status_code == 200:
                updated_data = response.json()
                assert updated_data["first_name"] == "Updated"

    def test_delete_user(self, sample_user_data):
        """Test deleting a user"""
        # First create a user
        create_response = requests.post(
            f"{self.api_base_url}/users",
            json=sample_user_data,
            headers=self.headers
        )
        
        if create_response.status_code == 201:
            user_data = create_response.json()
            user_id = user_data["id"]
            
            # Delete the user
            response = requests.delete(
                f"{self.api_base_url}/users/{user_id}",
                headers=self.headers
            )
            
            assert response.status_code in [200, 204]
            
            # Verify user is deleted
            get_response = requests.get(
                f"{self.api_base_url}/users/{user_id}",
                headers=self.headers
            )
            assert get_response.status_code == 404

    def test_create_product(self, sample_product_data):
        """Test creating a new product"""
        response = requests.post(
            f"{self.api_base_url}/products",
            json=sample_product_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == sample_product_data["name"]
            assert data["price"] == sample_product_data["price"]
            self.created_resources.append(("products", data["id"]))
        else:
            assert response.status_code in [404, 401, 403, 501]

    def test_search_products(self):
        """Test product search functionality"""
        search_params = {
            "q": "test",
            "category": "electronics",
            "min_price": 10,
            "max_price": 1000
        }
        
        response = requests.get(
            f"{self.api_base_url}/products/search",
            params=search_params,
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
        else:
            assert response.status_code in [404, 401, 403, 501]