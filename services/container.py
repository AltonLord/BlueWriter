"""
Service Container for BlueWriter.

Provides centralized initialization and access to all services.
"""
from typing import Dict, Any

from events.event_bus import EventBus
from services.project_service import ProjectService
from services.story_service import StoryService
from services.chapter_service import ChapterService
from services.encyclopedia_service import EncyclopediaService
from services.canvas_service import CanvasService
from services.editor_service import EditorService


class ServiceContainer:
    """
    Container for all BlueWriter services.
    
    Provides centralized initialization and access to services,
    event bus, and related infrastructure.
    
    Usage:
        container = ServiceContainer(db_path)
        projects = container.project.list_projects()
        container.start_api_server()
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the service container.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        
        # Create event bus
        self.event_bus = EventBus()
        
        # Create all services
        self.project = ProjectService(db_path, self.event_bus)
        self.story = StoryService(db_path, self.event_bus)
        self.chapter = ChapterService(db_path, self.event_bus)
        self.encyclopedia = EncyclopediaService(db_path, self.event_bus)
        self.canvas = CanvasService(self.event_bus)
        self.editor = EditorService(self.event_bus)
        
        # API server state
        self._api_thread = None
        self._api_port = 5000
    
    def get_services_dict(self) -> Dict[str, Any]:
        """Get services as a dictionary (for API initialization)."""
        return {
            'project': self.project,
            'story': self.story,
            'chapter': self.chapter,
            'encyclopedia': self.encyclopedia,
            'canvas': self.canvas,
            'editor': self.editor,
        }
    
    def start_api_server(self, port: int = 5000) -> None:
        """Start the REST API server in a background thread.
        
        Args:
            port: Port to listen on (default: 5000)
        """
        from api.launcher import start_api_server
        
        self._api_port = port
        self._api_thread = start_api_server(
            services=self.get_services_dict(),
            port=port,
        )
    
    def is_api_running(self) -> bool:
        """Check if the API server is running."""
        return self._api_thread is not None and self._api_thread.is_alive()
    
    def get_api_url(self) -> str:
        """Get the API server URL."""
        return f"http://127.0.0.1:{self._api_port}"


__all__ = ['ServiceContainer']
