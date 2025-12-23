"""
Integration tests for Projects API endpoints.

Tests all project CRUD operations via the REST API.
"""
import pytest
from fastapi.testclient import TestClient

from api.server import create_app


class TestProjectsAPI:
    """Test cases for /projects endpoints."""
    
    @pytest.fixture
    def client(self, all_services) -> TestClient:
        """Create test client with services."""
        app = create_app(all_services)
        return TestClient(app)
    
    # =========================================================================
    # List Projects
    # =========================================================================
    
    def test_list_projects_empty(self, client):
        """Test listing projects when none exist."""
        response = client.get("/projects")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_projects(self, client):
        """Test listing multiple projects."""
        # Create some projects
        client.post("/projects", json={"name": "Project A"})
        client.post("/projects", json={"name": "Project B"})
        
        response = client.get("/projects")
        
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 2
    
    # =========================================================================
    # Create Project
    # =========================================================================
    
    def test_create_project(self, client):
        """Test creating a project."""
        response = client.post("/projects", json={
            "name": "My Novel",
            "description": "A great story"
        })
        
        assert response.status_code == 201
        project = response.json()
        assert project["name"] == "My Novel"
        assert project["description"] == "A great story"
        assert "id" in project
        assert "created_at" in project
    
    def test_create_project_minimal(self, client):
        """Test creating a project with only name."""
        response = client.post("/projects", json={"name": "Minimal"})
        
        assert response.status_code == 201
        project = response.json()
        assert project["name"] == "Minimal"
    
    def test_create_project_empty_name_fails(self, client):
        """Test that empty name returns 422."""
        response = client.post("/projects", json={"name": ""})
        
        assert response.status_code == 422
    
    def test_create_project_missing_name_fails(self, client):
        """Test that missing name returns 422."""
        response = client.post("/projects", json={})
        
        assert response.status_code == 422
    
    # =========================================================================
    # Get Project
    # =========================================================================
    
    def test_get_project(self, client):
        """Test getting a project by ID."""
        # Create a project first
        create_response = client.post("/projects", json={
            "name": "Get Test",
            "description": "Test description"
        })
        project_id = create_response.json()["id"]
        
        response = client.get(f"/projects/{project_id}")
        
        assert response.status_code == 200
        project = response.json()
        assert project["id"] == project_id
        assert project["name"] == "Get Test"
    
    def test_get_project_not_found(self, client):
        """Test getting a non-existent project returns 404."""
        response = client.get("/projects/99999")
        
        assert response.status_code == 404
    
    # =========================================================================
    # Update Project
    # =========================================================================
    
    def test_update_project_name(self, client):
        """Test updating project name."""
        create_response = client.post("/projects", json={"name": "Original"})
        project_id = create_response.json()["id"]
        
        response = client.put(f"/projects/{project_id}", json={
            "name": "Updated"
        })
        
        assert response.status_code == 200
        project = response.json()
        assert project["name"] == "Updated"
    
    def test_update_project_description(self, client):
        """Test updating project description."""
        create_response = client.post("/projects", json={
            "name": "Test",
            "description": "Old"
        })
        project_id = create_response.json()["id"]
        
        response = client.put(f"/projects/{project_id}", json={
            "description": "New description"
        })
        
        assert response.status_code == 200
        project = response.json()
        assert project["description"] == "New description"
        assert project["name"] == "Test"  # Unchanged
    
    def test_update_project_not_found(self, client):
        """Test updating a non-existent project returns 404."""
        response = client.put("/projects/99999", json={"name": "New"})
        
        assert response.status_code == 404
    
    # =========================================================================
    # Delete Project
    # =========================================================================
    
    def test_delete_project(self, client):
        """Test deleting a project."""
        create_response = client.post("/projects", json={"name": "To Delete"})
        project_id = create_response.json()["id"]
        
        response = client.delete(f"/projects/{project_id}")
        
        assert response.status_code == 200  # API returns 200 with confirmation
        
        # Verify it's gone
        get_response = client.get(f"/projects/{project_id}")
        assert get_response.status_code == 404
    
    def test_delete_project_not_found(self, client):
        """Test deleting a non-existent project returns 404."""
        response = client.delete("/projects/99999")
        
        assert response.status_code == 404


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.fixture
    def client(self, all_services) -> TestClient:
        """Create test client with services."""
        app = create_app(all_services)
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns OK."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
