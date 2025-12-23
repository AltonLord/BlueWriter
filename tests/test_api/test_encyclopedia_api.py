"""
Integration tests for Encyclopedia API endpoints.

Tests all encyclopedia CRUD and search operations via the REST API.
"""
import pytest
from fastapi.testclient import TestClient

from api.server import create_app


class TestEncyclopediaAPI:
    """Test cases for /encyclopedia endpoints."""
    
    @pytest.fixture
    def client(self, all_services) -> TestClient:
        """Create test client with services."""
        app = create_app(all_services)
        return TestClient(app)
    
    @pytest.fixture
    def project_id(self, client) -> int:
        """Create a project and return its ID."""
        response = client.post("/projects", json={"name": "Test Project"})
        return response.json()["id"]
    
    # =========================================================================
    # List Entries
    # =========================================================================
    
    def test_list_entries_empty(self, client, project_id):
        """Test listing entries when none exist."""
        response = client.get(f"/projects/{project_id}/encyclopedia")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_entries(self, client, project_id):
        """Test listing multiple entries."""
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Hero", "category": "Character"
        })
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Castle", "category": "Location"
        })
        
        response = client.get(f"/projects/{project_id}/encyclopedia")
        
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) == 2
    
    def test_list_entries_by_category(self, client, project_id):
        """Test filtering entries by category."""
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Hero", "category": "Character"
        })
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Villain", "category": "Character"
        })
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Castle", "category": "Location"
        })
        
        response = client.get(
            f"/projects/{project_id}/encyclopedia",
            params={"category": "Character"}
        )
        
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) == 2
        assert all(e["category"] == "Character" for e in entries)
    
    # =========================================================================
    # Create Entry
    # =========================================================================
    
    def test_create_entry(self, client, project_id):
        """Test creating an entry."""
        response = client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Dragon",
            "category": "Creature",
            "content": "A fire-breathing beast",
            "tags": "monster, flying"
        })
        
        assert response.status_code == 201
        entry = response.json()
        assert entry["name"] == "Dragon"
        assert entry["category"] == "Creature"
        assert entry["content"] == "A fire-breathing beast"
        assert entry["tags"] == "monster, flying"
    
    def test_create_entry_minimal(self, client, project_id):
        """Test creating an entry with minimal data."""
        response = client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Simple",
            "category": "Item"
        })
        
        assert response.status_code == 201
        entry = response.json()
        assert entry["name"] == "Simple"
        assert entry["category"] == "Item"
    
    # =========================================================================
    # Get Entry
    # =========================================================================
    
    def test_get_entry(self, client, project_id):
        """Test getting an entry by ID."""
        create_response = client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Get Test",
            "category": "Character"
        })
        entry_id = create_response.json()["id"]
        
        response = client.get(f"/encyclopedia/{entry_id}")
        
        assert response.status_code == 200
        entry = response.json()
        assert entry["id"] == entry_id
        assert entry["name"] == "Get Test"
    
    def test_get_entry_not_found(self, client):
        """Test getting a non-existent entry returns 404."""
        response = client.get("/encyclopedia/99999")
        
        assert response.status_code == 404
    
    # =========================================================================
    # Update Entry
    # =========================================================================
    
    def test_update_entry_name(self, client, project_id):
        """Test updating entry name."""
        create_response = client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Original",
            "category": "Character"
        })
        entry_id = create_response.json()["id"]
        
        response = client.put(f"/encyclopedia/{entry_id}", json={
            "name": "Updated"
        })
        
        assert response.status_code == 200
        entry = response.json()
        assert entry["name"] == "Updated"
    
    def test_update_entry_content(self, client, project_id):
        """Test updating entry content."""
        create_response = client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Test",
            "category": "Character"
        })
        entry_id = create_response.json()["id"]
        
        response = client.put(f"/encyclopedia/{entry_id}", json={
            "content": "New description here"
        })
        
        assert response.status_code == 200
        entry = response.json()
        assert entry["content"] == "New description here"
    
    # =========================================================================
    # Delete Entry
    # =========================================================================
    
    def test_delete_entry(self, client, project_id):
        """Test deleting an entry."""
        create_response = client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "To Delete",
            "category": "Item"
        })
        entry_id = create_response.json()["id"]
        
        response = client.delete(f"/encyclopedia/{entry_id}")
        
        assert response.status_code == 200  # API returns 200 with confirmation
        
        # Verify it's gone
        get_response = client.get(f"/encyclopedia/{entry_id}")
        assert get_response.status_code == 404
    
    # =========================================================================
    # Search
    # =========================================================================
    
    def test_search_entries(self, client, project_id):
        """Test searching entries."""
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Dragon Lord",
            "category": "Character"
        })
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Dragon Cave",
            "category": "Location"
        })
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Magic Sword",
            "category": "Item"
        })
        
        response = client.get(
            f"/projects/{project_id}/encyclopedia/search",
            params={"q": "Dragon"}
        )
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        assert all("Dragon" in e["name"] for e in results)
    
    def test_search_entries_no_results(self, client, project_id):
        """Test searching with no matches."""
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Hero",
            "category": "Character"
        })
        
        response = client.get(
            f"/projects/{project_id}/encyclopedia/search",
            params={"q": "nonexistent"}
        )
        
        assert response.status_code == 200
        assert response.json() == []
    
    # =========================================================================
    # Categories
    # =========================================================================
    
    def test_list_categories(self, client, project_id):
        """Test listing all categories in use."""
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Hero", "category": "Character"
        })
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Castle", "category": "Location"
        })
        client.post(f"/projects/{project_id}/encyclopedia", json={
            "name": "Villain", "category": "Character"
        })
        
        response = client.get(f"/projects/{project_id}/encyclopedia/categories")
        
        assert response.status_code == 200
        categories = response.json()
        # Returns default categories plus used ones
        assert "Character" in categories
        assert "Location" in categories
        assert len(categories) >= 2  # At least the ones we used, plus defaults
