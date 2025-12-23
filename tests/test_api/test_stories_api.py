"""
Integration tests for Stories API endpoints.

Tests all story CRUD and publishing operations via the REST API.
"""
import pytest
from fastapi.testclient import TestClient

from api.server import create_app


class TestStoriesAPI:
    """Test cases for /stories endpoints."""
    
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
    # List Stories
    # =========================================================================
    
    def test_list_stories_empty(self, client, project_id):
        """Test listing stories when none exist."""
        response = client.get(f"/projects/{project_id}/stories")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_stories(self, client, project_id):
        """Test listing multiple stories."""
        client.post(f"/projects/{project_id}/stories", json={"title": "Story A"})
        client.post(f"/projects/{project_id}/stories", json={"title": "Story B"})
        
        response = client.get(f"/projects/{project_id}/stories")
        
        assert response.status_code == 200
        stories = response.json()
        assert len(stories) == 2
    
    # =========================================================================
    # Create Story
    # =========================================================================
    
    def test_create_story(self, client, project_id):
        """Test creating a story."""
        response = client.post(f"/projects/{project_id}/stories", json={
            "title": "My Story",
            "synopsis": "An adventure"
        })
        
        assert response.status_code == 201
        story = response.json()
        assert story["title"] == "My Story"
        assert story["synopsis"] == "An adventure"
        assert story["status"] == "draft"
        assert "id" in story
    
    def test_create_story_empty_title_fails(self, client, project_id):
        """Test that empty title returns 422."""
        response = client.post(f"/projects/{project_id}/stories", json={
            "title": ""
        })
        
        assert response.status_code == 422
    
    # =========================================================================
    # Get Story
    # =========================================================================
    
    def test_get_story(self, client, project_id):
        """Test getting a story by ID."""
        create_response = client.post(f"/projects/{project_id}/stories", json={
            "title": "Get Test"
        })
        story_id = create_response.json()["id"]
        
        response = client.get(f"/stories/{story_id}")
        
        assert response.status_code == 200
        story = response.json()
        assert story["id"] == story_id
        assert story["title"] == "Get Test"
    
    def test_get_story_not_found(self, client):
        """Test getting a non-existent story returns 404."""
        response = client.get("/stories/99999")
        
        assert response.status_code == 404
    
    # =========================================================================
    # Update Story
    # =========================================================================
    
    def test_update_story_title(self, client, project_id):
        """Test updating story title."""
        create_response = client.post(f"/projects/{project_id}/stories", json={
            "title": "Original"
        })
        story_id = create_response.json()["id"]
        
        response = client.put(f"/stories/{story_id}", json={
            "title": "Updated"
        })
        
        assert response.status_code == 200
        story = response.json()
        assert story["title"] == "Updated"
    
    def test_update_story_not_found(self, client):
        """Test updating a non-existent story returns 404."""
        response = client.put("/stories/99999", json={"title": "New"})
        
        assert response.status_code == 404
    
    # =========================================================================
    # Delete Story
    # =========================================================================
    
    def test_delete_story(self, client, project_id):
        """Test deleting a story."""
        create_response = client.post(f"/projects/{project_id}/stories", json={
            "title": "To Delete"
        })
        story_id = create_response.json()["id"]
        
        response = client.delete(f"/stories/{story_id}")
        
        assert response.status_code == 200  # API returns 200 with confirmation
        
        # Verify it's gone
        get_response = client.get(f"/stories/{story_id}")
        assert get_response.status_code == 404
    
    # =========================================================================
    # Publishing
    # =========================================================================
    
    def test_publish_story_rough(self, client, project_id):
        """Test rough publishing a story."""
        create_response = client.post(f"/projects/{project_id}/stories", json={
            "title": "To Publish"
        })
        story_id = create_response.json()["id"]
        
        response = client.post(f"/stories/{story_id}/publish", json={
            "final": False
        })
        
        assert response.status_code == 200
        story = response.json()
        assert story["status"] == "rough_published"
    
    def test_publish_story_final(self, client, project_id):
        """Test final publishing a story."""
        create_response = client.post(f"/projects/{project_id}/stories", json={
            "title": "To Publish Final"
        })
        story_id = create_response.json()["id"]
        
        response = client.post(f"/stories/{story_id}/publish", json={
            "final": True
        })
        
        assert response.status_code == 200
        story = response.json()
        assert story["status"] == "final_published"
    
    def test_unpublish_story(self, client, project_id):
        """Test unpublishing a story."""
        create_response = client.post(f"/projects/{project_id}/stories", json={
            "title": "To Unpublish"
        })
        story_id = create_response.json()["id"]
        
        # First publish
        client.post(f"/stories/{story_id}/publish", json={"final": True})
        
        # Then unpublish
        response = client.post(f"/stories/{story_id}/unpublish")
        
        assert response.status_code == 200
        story = response.json()
        assert story["status"] == "draft"
    
    def test_cannot_update_final_published(self, client, project_id):
        """Test that final published stories cannot be updated."""
        create_response = client.post(f"/projects/{project_id}/stories", json={
            "title": "Locked"
        })
        story_id = create_response.json()["id"]
        
        # Publish final
        client.post(f"/stories/{story_id}/publish", json={"final": True})
        
        # Try to update
        response = client.put(f"/stories/{story_id}", json={
            "title": "New Title"
        })
        
        assert response.status_code == 409  # Conflict
    
    # =========================================================================
    # Reorder Stories
    # =========================================================================
    
    def test_reorder_stories(self, client, project_id):
        """Test reordering stories."""
        s1 = client.post(f"/projects/{project_id}/stories", json={"title": "First"}).json()
        s2 = client.post(f"/projects/{project_id}/stories", json={"title": "Second"}).json()
        s3 = client.post(f"/projects/{project_id}/stories", json={"title": "Third"}).json()
        
        # Reorder: Third, First, Second
        response = client.put(f"/projects/{project_id}/stories/order", json={
            "story_ids": [s3["id"], s1["id"], s2["id"]]
        })
        
        assert response.status_code == 200
        
        # Verify order
        stories = client.get(f"/projects/{project_id}/stories").json()
        assert stories[0]["id"] == s3["id"]
        assert stories[1]["id"] == s1["id"]
        assert stories[2]["id"] == s2["id"]
