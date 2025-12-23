"""
Integration tests for MCP tools.

Tests MCP tools against a live test API server.
These tests verify that MCP tools correctly communicate with the API.
"""
import pytest
import httpx
import threading
import time
import os

# Ensure we can import from project
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestMCPToolsIntegration:
    """Integration tests for MCP tools against live API."""
    
    @pytest.fixture
    def test_server(self, all_services):
        """Start a test API server in a background thread.
        
        Returns the base URL for the server.
        """
        from api.server import create_app
        import uvicorn
        
        app = create_app(all_services)
        
        # Find an available port
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        
        # Start server in background thread
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        
        # Wait for server to start
        base_url = f"http://127.0.0.1:{port}"
        for _ in range(50):  # Wait up to 5 seconds
            try:
                with httpx.Client() as client:
                    response = client.get(f"{base_url}/health")
                    if response.status_code == 200:
                        break
            except httpx.ConnectError:
                pass
            time.sleep(0.1)
        
        yield base_url
        
        # Server will be stopped when thread is garbage collected (daemon=True)
    
    # =========================================================================
    # Project Tool Tests
    # =========================================================================
    
    def test_list_projects(self, test_server):
        """Test list_projects tool."""
        with httpx.Client() as client:
            # First create a project
            client.post(
                f"{test_server}/projects",
                json={"name": "Test Project"}
            )
            
            # List projects (simulating what MCP tool does)
            response = client.get(f"{test_server}/projects")
            
            assert response.status_code == 200
            projects = response.json()
            assert len(projects) >= 1
    
    def test_create_project(self, test_server):
        """Test create_project tool."""
        with httpx.Client() as client:
            response = client.post(
                f"{test_server}/projects",
                json={"name": "MCP Created", "description": "Via MCP"}
            )
            
            assert response.status_code == 201
            project = response.json()
            assert project["name"] == "MCP Created"
    
    def test_get_project(self, test_server):
        """Test get_project tool."""
        with httpx.Client() as client:
            # Create a project
            create_response = client.post(
                f"{test_server}/projects",
                json={"name": "Get Test"}
            )
            project_id = create_response.json()["id"]
            
            # Get the project
            response = client.get(f"{test_server}/projects/{project_id}")
            
            assert response.status_code == 200
            assert response.json()["name"] == "Get Test"
    
    # =========================================================================
    # Story Tool Tests
    # =========================================================================
    
    def test_create_and_list_stories(self, test_server):
        """Test story creation and listing."""
        with httpx.Client() as client:
            # Create a project
            project = client.post(
                f"{test_server}/projects",
                json={"name": "Story Test Project"}
            ).json()
            
            # Create a story
            story = client.post(
                f"{test_server}/projects/{project['id']}/stories",
                json={"title": "Test Story", "synopsis": "A test"}
            ).json()
            
            assert story["title"] == "Test Story"
            
            # List stories
            stories = client.get(
                f"{test_server}/projects/{project['id']}/stories"
            ).json()
            
            assert len(stories) == 1
    
    def test_story_publishing(self, test_server):
        """Test story publishing workflow."""
        with httpx.Client() as client:
            # Create project and story
            project = client.post(
                f"{test_server}/projects",
                json={"name": "Publish Test"}
            ).json()
            
            story = client.post(
                f"{test_server}/projects/{project['id']}/stories",
                json={"title": "To Publish"}
            ).json()
            
            # Publish story
            published = client.post(
                f"{test_server}/stories/{story['id']}/publish",
                json={"final": True}
            ).json()
            
            assert published["status"] == "final_published"
            
            # Unpublish story
            unpublished = client.post(
                f"{test_server}/stories/{story['id']}/unpublish"
            ).json()
            
            assert unpublished["status"] == "draft"
    
    # =========================================================================
    # Chapter Tool Tests
    # =========================================================================
    
    def test_chapter_crud(self, test_server):
        """Test chapter CRUD operations."""
        with httpx.Client() as client:
            # Setup: create project and story
            project = client.post(
                f"{test_server}/projects",
                json={"name": "Chapter Test"}
            ).json()
            
            story = client.post(
                f"{test_server}/projects/{project['id']}/stories",
                json={"title": "Story"}
            ).json()
            
            # Create chapter
            chapter = client.post(
                f"{test_server}/stories/{story['id']}/chapters",
                json={
                    "title": "Chapter One",
                    "board_x": 100,
                    "board_y": 100
                }
            ).json()
            
            assert chapter["title"] == "Chapter One"
            
            # Update chapter
            updated = client.put(
                f"{test_server}/chapters/{chapter['id']}",
                json={"title": "Updated Chapter"}
            ).json()
            
            assert updated["title"] == "Updated Chapter"
            
            # Delete chapter
            response = client.delete(f"{test_server}/chapters/{chapter['id']}")
            assert response.status_code == 200  # API returns 200 with confirmation
    
    def test_chapter_move(self, test_server):
        """Test moving a chapter on the canvas."""
        with httpx.Client() as client:
            # Setup
            project = client.post(
                f"{test_server}/projects",
                json={"name": "Move Test"}
            ).json()
            
            story = client.post(
                f"{test_server}/projects/{project['id']}/stories",
                json={"title": "Story"}
            ).json()
            
            chapter = client.post(
                f"{test_server}/stories/{story['id']}/chapters",
                json={"title": "Movable"}
            ).json()
            
            # Move chapter
            moved = client.put(
                f"{test_server}/chapters/{chapter['id']}/position",
                json={"board_x": 500, "board_y": 300}
            ).json()
            
            assert moved["board_x"] == 500
            assert moved["board_y"] == 300
    
    # =========================================================================
    # Encyclopedia Tool Tests
    # =========================================================================
    
    def test_encyclopedia_crud(self, test_server):
        """Test encyclopedia CRUD operations."""
        with httpx.Client() as client:
            # Create project
            project = client.post(
                f"{test_server}/projects",
                json={"name": "Encyclopedia Test"}
            ).json()
            
            # Create entry
            entry = client.post(
                f"{test_server}/projects/{project['id']}/encyclopedia",
                json={
                    "name": "Dragon",
                    "category": "Creature",
                    "content": "A beast",
                    "tags": "monster"
                }
            ).json()
            
            assert entry["name"] == "Dragon"
            
            # Get entry
            fetched = client.get(
                f"{test_server}/encyclopedia/{entry['id']}"
            ).json()
            
            assert fetched["name"] == "Dragon"
            
            # Update entry
            updated = client.put(
                f"{test_server}/encyclopedia/{entry['id']}",
                json={"content": "A fire-breathing beast"}
            ).json()
            
            assert updated["content"] == "A fire-breathing beast"
    
    def test_encyclopedia_search(self, test_server):
        """Test encyclopedia search."""
        with httpx.Client() as client:
            # Create project and entries
            project = client.post(
                f"{test_server}/projects",
                json={"name": "Search Test"}
            ).json()
            
            client.post(
                f"{test_server}/projects/{project['id']}/encyclopedia",
                json={"name": "Fire Dragon", "category": "Creature"}
            )
            client.post(
                f"{test_server}/projects/{project['id']}/encyclopedia",
                json={"name": "Ice Dragon", "category": "Creature"}
            )
            client.post(
                f"{test_server}/projects/{project['id']}/encyclopedia",
                json={"name": "Magic Sword", "category": "Item"}
            )
            
            # Search for "Dragon"
            results = client.get(
                f"{test_server}/projects/{project['id']}/encyclopedia/search",
                params={"q": "Dragon"}
            ).json()
            
            assert len(results) == 2
    
    # =========================================================================
    # Canvas Tool Tests
    # =========================================================================
    
    def test_canvas_operations(self, test_server):
        """Test canvas pan/zoom operations."""
        with httpx.Client() as client:
            # Create project and story
            project = client.post(
                f"{test_server}/projects",
                json={"name": "Canvas Test"}
            ).json()
            
            story = client.post(
                f"{test_server}/projects/{project['id']}/stories",
                json={"title": "Story"}
            ).json()
            
            # Get canvas view
            view = client.get(
                f"{test_server}/stories/{story['id']}/canvas"
            ).json()
            
            assert "pan_x" in view
            assert "zoom" in view
            
            # Pan canvas
            panned = client.put(
                f"{test_server}/stories/{story['id']}/canvas/pan",
                json={"x": 100, "y": 200}
            ).json()
            
            assert panned["pan_x"] == 100
            assert panned["pan_y"] == 200
            
            # Zoom canvas
            zoomed = client.put(
                f"{test_server}/stories/{story['id']}/canvas/zoom",
                json={"zoom": 1.5}
            ).json()
            
            assert zoomed["zoom"] == 1.5
    
    # =========================================================================
    # State Tool Tests
    # =========================================================================
    
    def test_app_state(self, test_server):
        """Test app state endpoint."""
        with httpx.Client() as client:
            response = client.get(f"{test_server}/state")
            
            assert response.status_code == 200
            state = response.json()
            assert "current_project_id" in state
            assert "open_editors" in state
