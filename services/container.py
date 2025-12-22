"""
Service initialization for BlueWriter.

Provides factory functions to create and wire up all services
with the event bus and Qt adapter.
"""
from typing import Dict, Any, Optional
from pathlib import Path

from events.event_bus import EventBus
from services.project_service import ProjectService
from services.story_service import StoryService
from services.chapter_service import ChapterService
from services.encyclopedia_service import EncyclopediaService
from services.canvas_service import CanvasService
from services.editor_service import EditorService


def create_services(db_path: str, event_bus: EventBus) -> Dict[str, Any]:
    """Create all service instances.
    
    Args:
        db_path: Path to the SQLite database
        event_bus: EventBus for publishing events
        
    Returns:
        Dictionary of service instances keyed by name
    """
    return {
        'project': ProjectService(db_path, event_bus),
        'story': StoryService(db_path, event_bus),
        'chapter': ChapterService(db_path, event_bus),
        'encyclopedia': EncyclopediaService(db_path, event_bus),
        'canvas': CanvasService(event_bus),
        'editor': EditorService(event_bus),
    }


class ServiceContainer:
    """Container for all BlueWriter services.
    
    Provides convenient access to services and manages their lifecycle.
    
    Usage:
        container = ServiceContainer(db_path)
        projects = container.project.list_projects()
        container.chapter.create_chapter(...)
    """
    
    def __init__(self, db_path: str, event_bus: Optional[EventBus] = None):
        """Initialize the service container.
        
        Args:
            db_path: Path to the SQLite database
            event_bus: Optional EventBus (creates one if not provided)
        """
        self.db_path = db_path
        self.event_bus = event_bus or EventBus()
        self._services = create_services(db_path, self.event_bus)
    
    @property
    def project(self) -> ProjectService:
        """Get the ProjectService."""
        return self._services['project']
    
    @property
    def story(self) -> StoryService:
        """Get the StoryService."""
        return self._services['story']
    
    @property
    def chapter(self) -> ChapterService:
        """Get the ChapterService."""
        return self._services['chapter']
    
    @property
    def encyclopedia(self) -> EncyclopediaService:
        """Get the EncyclopediaService."""
        return self._services['encyclopedia']
    
    @property
    def canvas(self) -> CanvasService:
        """Get the CanvasService."""
        return self._services['canvas']
    
    @property
    def editor(self) -> EditorService:
        """Get the EditorService."""
        return self._services['editor']
    
    def as_dict(self) -> Dict[str, Any]:
        """Get all services as a dictionary (for API injection)."""
        return self._services.copy()
    
    def start_api_server(self, host: str = "127.0.0.1", port: int = 5000) -> None:
        """Start the REST API server in a background thread.
        
        Args:
            host: Host to bind to (default: localhost)
            port: Port to listen on (default: 5000)
        """
        from api.startup import start_api_server
        self._api_host = host
        self._api_port = port
        self._api_thread = start_api_server(self._services, host, port)
    
    def get_api_url(self) -> str:
        """Get the URL where the API server is running."""
        host = getattr(self, '_api_host', '127.0.0.1')
        port = getattr(self, '_api_port', 5000)
        return f"http://{host}:{port}"
    
    def is_api_running(self) -> bool:
        """Check if the API server is running."""
        thread = getattr(self, '_api_thread', None)
        return thread is not None and thread.is_alive()


__all__ = ['create_services', 'ServiceContainer']
