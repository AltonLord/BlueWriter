"""
Integration tests for Chapters API endpoints.

Tests all chapter CRUD and content operations via the REST API.
"""
import pytest
from fastapi.testclient import TestClient

from api.server import create_app


class TestChaptersAPI:
    """Test cases for /chapters endpoints."""
    
    @pytest.fixture
    def client(self, all_services) -> TestClient:
        """Create test client with services."""
        app = create_app(all_services)
        return TestClient(app)
    
    @pytest.fixture
    def story_id(self, client) -> int:
        """Create a project and story, return story ID."""
        project = client.post("/projects", json={"name": "Test Project"}).json()
        story = client.post(f"/projects/{project['id']}/stories", json={
            "title": "Test Story"
        }).json()
        return story["id"]
    
    # =========================================================================
    # List Chapters
    # =========================================================================
    
    def test_list_chapters_empty(self, client, story_id):
        """Test listing chapters when none exist."""
        response = client.get(f"/stories/{story_id}/chapters")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_chapters(self, client, story_id):
        """Test listing multiple chapters."""
        client.post(f"/stories/{story_id}/chapters", json={"title": "Chapter 1"})
        client.post(f"/stories/{story_id}/chapters", json={"title": "Chapter 2"})
        
        response = client.get(f"/stories/{story_id}/chapters")
        
        assert response.status_code == 200
        chapters = response.json()
        assert len(chapters) == 2
    
    # =========================================================================
    # Create Chapter
    # =========================================================================
    
    def test_create_chapter(self, client, story_id):
        """Test creating a chapter."""
        response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "My Chapter",
            "board_x": 150,
            "board_y": 200,
            "color": "#FF8888"
        })
        
        assert response.status_code == 201
        chapter = response.json()
        assert chapter["title"] == "My Chapter"
        assert chapter["board_x"] == 150
        assert chapter["board_y"] == 200
        assert chapter["color"] == "#FF8888"
    
    def test_create_chapter_defaults(self, client, story_id):
        """Test creating a chapter with default values."""
        response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Defaults"
        })
        
        assert response.status_code == 201
        chapter = response.json()
        assert chapter["board_x"] == 100  # Default
        assert chapter["board_y"] == 100  # Default
        assert chapter["color"] == "#FFFF88"  # Default yellow
    
    def test_create_chapter_invalid_color_fails(self, client, story_id):
        """Test that invalid color format returns 422."""
        response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Bad Color",
            "color": "red"
        })
        
        assert response.status_code == 422
    
    # =========================================================================
    # Get Chapter
    # =========================================================================
    
    def test_get_chapter(self, client, story_id):
        """Test getting a chapter by ID."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Get Test"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.get(f"/chapters/{chapter_id}")
        
        assert response.status_code == 200
        chapter = response.json()
        assert chapter["id"] == chapter_id
        assert chapter["title"] == "Get Test"
    
    def test_get_chapter_not_found(self, client):
        """Test getting a non-existent chapter returns 404."""
        response = client.get("/chapters/99999")
        
        assert response.status_code == 404
    
    # =========================================================================
    # Update Chapter
    # =========================================================================
    
    def test_update_chapter_title(self, client, story_id):
        """Test updating chapter title."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Original"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.put(f"/chapters/{chapter_id}", json={
            "title": "Updated"
        })
        
        assert response.status_code == 200
        chapter = response.json()
        assert chapter["title"] == "Updated"
    
    def test_update_chapter_summary(self, client, story_id):
        """Test updating chapter summary."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Test"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.put(f"/chapters/{chapter_id}", json={
            "summary": "A brief summary"
        })
        
        assert response.status_code == 200
        chapter = response.json()
        assert chapter["summary"] == "A brief summary"
    
    # =========================================================================
    # Move Chapter
    # =========================================================================
    
    def test_move_chapter(self, client, story_id):
        """Test moving a chapter on the canvas."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Movable"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.put(f"/chapters/{chapter_id}/position", json={
            "board_x": 500,
            "board_y": 300
        })
        
        assert response.status_code == 200
        chapter = response.json()
        assert chapter["board_x"] == 500
        assert chapter["board_y"] == 300
    
    def test_move_chapter_negative_coords(self, client, story_id):
        """Test moving a chapter to negative coordinates."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Negative"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.put(f"/chapters/{chapter_id}/position", json={
            "board_x": -100,
            "board_y": -50
        })
        
        assert response.status_code == 200
        chapter = response.json()
        assert chapter["board_x"] == -100
        assert chapter["board_y"] == -50
    
    # =========================================================================
    # Chapter Color
    # =========================================================================
    
    def test_set_chapter_color(self, client, story_id):
        """Test changing chapter color."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Colorful"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.put(f"/chapters/{chapter_id}/color", json={
            "color": "#88FF88"
        })
        
        assert response.status_code == 200
        chapter = response.json()
        assert chapter["color"] == "#88FF88"
    
    # =========================================================================
    # Delete Chapter
    # =========================================================================
    
    def test_delete_chapter(self, client, story_id):
        """Test deleting a chapter."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "To Delete"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.delete(f"/chapters/{chapter_id}")
        
        assert response.status_code == 200  # API returns 200 with confirmation
        
        # Verify it's gone
        get_response = client.get(f"/chapters/{chapter_id}")
        assert get_response.status_code == 404
    
    # =========================================================================
    # Content Operations
    # =========================================================================
    
    def test_update_chapter_content(self, client, story_id):
        """Test updating chapter content."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Content Test"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.put(f"/chapters/{chapter_id}/content", json={
            "content": "<p>Chapter content here.</p>",
            "format": "html"
        })
        
        assert response.status_code == 200
        chapter = response.json()
        assert "<p>" in chapter["content"]
    
    def test_get_chapter_text(self, client, story_id):
        """Test getting chapter as plain text."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Text Test"
        })
        chapter_id = create_response.json()["id"]
        
        # Set HTML content
        client.put(f"/chapters/{chapter_id}/content", json={
            "content": "<p>Plain text content.</p>",
            "format": "html"
        })
        
        response = client.get(f"/chapters/{chapter_id}/text")
        
        assert response.status_code == 200
        # Should return plain text without HTML tags
        text = response.json()
        assert "<p>" not in str(text)
    
    def test_insert_scene_break(self, client, story_id):
        """Test inserting a scene break."""
        create_response = client.post(f"/stories/{story_id}/chapters", json={
            "title": "Scene Break Test"
        })
        chapter_id = create_response.json()["id"]
        
        response = client.post(f"/chapters/{chapter_id}/scene-break", json={
            "position": -1
        })
        
        assert response.status_code == 200
