"""
BlueWriter Test Configuration and Fixtures.

This module provides shared fixtures for all tests including:
- In-memory test database with schema
- Event bus for testing event emissions
- Service instances with test database
- Sample data factories
"""
import sqlite3
import tempfile
import os
from typing import Generator, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import pytest

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import create_all_tables
from events.event_bus import EventBus
from events.events import Event


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for testing.
    
    Yields:
        Path to temporary SQLite database file
        
    The file is automatically cleaned up after the test.
    """
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize the database with schema
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    create_all_tables(conn)
    conn.close()
    
    yield path
    
    # Cleanup
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def test_db_connection(test_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Create a database connection for direct database testing.
    
    Args:
        test_db_path: Path to test database
        
    Yields:
        SQLite connection with foreign keys enabled
    """
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# =============================================================================
# Event Bus Fixtures
# =============================================================================

@dataclass
class RecordedEvent:
    """Wrapper for recorded events with metadata."""
    event: Event
    timestamp: datetime


class EventRecorder:
    """Records events for test assertions.
    
    Example:
        recorder = EventRecorder(event_bus)
        recorder.start()
        
        # ... do something that emits events ...
        
        recorder.stop()
        assert recorder.has_event(ProjectCreated)
        assert recorder.get_events(ProjectCreated)[0].project_id == 1
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.events: list[RecordedEvent] = []
        self._subscriptions: list = []
        self._recording = False
    
    def start(self) -> None:
        """Start recording all events."""
        if self._recording:
            return
        
        self._recording = True
        self.events.clear()
        
        # Subscribe to base Event class to catch everything
        # We need to subscribe to specific types since EventBus matches exact types
        from events.events import (
            ProjectCreated, ProjectUpdated, ProjectDeleted, ProjectOpened,
            StoryCreated, StoryUpdated, StoryDeleted, StorySelected,
            StoryPublished, StoryUnpublished, StoriesReordered,
            ChapterCreated, ChapterUpdated, ChapterDeleted, ChapterMoved,
            ChapterColorChanged, ChapterOpened, ChapterClosed,
            EntryCreated, EntryUpdated, EntryDeleted, EntryOpened, EntryClosed,
            CanvasPanned, CanvasZoomed,
            EditorStateChanged, EditorModifiedChanged,
            AppStateChanged, SaveRequested, SaveCompleted,
        )
        
        event_types = [
            ProjectCreated, ProjectUpdated, ProjectDeleted, ProjectOpened,
            StoryCreated, StoryUpdated, StoryDeleted, StorySelected,
            StoryPublished, StoryUnpublished, StoriesReordered,
            ChapterCreated, ChapterUpdated, ChapterDeleted, ChapterMoved,
            ChapterColorChanged, ChapterOpened, ChapterClosed,
            EntryCreated, EntryUpdated, EntryDeleted, EntryOpened, EntryClosed,
            CanvasPanned, CanvasZoomed,
            EditorStateChanged, EditorModifiedChanged,
            AppStateChanged, SaveRequested, SaveCompleted,
        ]
        
        for event_type in event_types:
            callback = self._make_callback()
            self.event_bus.subscribe(event_type, callback)
            self._subscriptions.append((event_type, callback))
    
    def _make_callback(self):
        """Create a callback that records events."""
        def callback(event: Event):
            self.events.append(RecordedEvent(
                event=event,
                timestamp=datetime.now()
            ))
        return callback
    
    def stop(self) -> None:
        """Stop recording events."""
        if not self._recording:
            return
        
        self._recording = False
        for event_type, callback in self._subscriptions:
            self.event_bus.unsubscribe(event_type, callback)
        self._subscriptions.clear()
    
    def clear(self) -> None:
        """Clear recorded events."""
        self.events.clear()
    
    def has_event(self, event_type: type) -> bool:
        """Check if an event of the given type was recorded."""
        return any(isinstance(rec.event, event_type) for rec in self.events)
    
    def get_events(self, event_type: type = None) -> list:
        """Get recorded events, optionally filtered by type.
        
        Args:
            event_type: If provided, only return events of this type
            
        Returns:
            List of Event objects (not RecordedEvent wrappers)
        """
        if event_type is None:
            return [rec.event for rec in self.events]
        return [rec.event for rec in self.events if isinstance(rec.event, event_type)]
    
    def count(self, event_type: type = None) -> int:
        """Count recorded events."""
        return len(self.get_events(event_type))


@pytest.fixture
def event_bus() -> EventBus:
    """Create a fresh EventBus for testing."""
    return EventBus()


@pytest.fixture
def event_recorder(event_bus: EventBus) -> Generator[EventRecorder, None, None]:
    """Create an event recorder that automatically records all events.
    
    Yields:
        EventRecorder that is already recording
    """
    recorder = EventRecorder(event_bus)
    recorder.start()
    yield recorder
    recorder.stop()


# =============================================================================
# Service Fixtures
# =============================================================================

@pytest.fixture
def project_service(test_db_path: str, event_bus: EventBus):
    """Create a ProjectService with test database."""
    from services.project_service import ProjectService
    return ProjectService(test_db_path, event_bus)


@pytest.fixture
def story_service(test_db_path: str, event_bus: EventBus):
    """Create a StoryService with test database."""
    from services.story_service import StoryService
    return StoryService(test_db_path, event_bus)


@pytest.fixture
def chapter_service(test_db_path: str, event_bus: EventBus):
    """Create a ChapterService with test database."""
    from services.chapter_service import ChapterService
    return ChapterService(test_db_path, event_bus)


@pytest.fixture
def encyclopedia_service(test_db_path: str, event_bus: EventBus):
    """Create an EncyclopediaService with test database."""
    from services.encyclopedia_service import EncyclopediaService
    return EncyclopediaService(test_db_path, event_bus)


@pytest.fixture
def canvas_service(event_bus: EventBus):
    """Create a CanvasService (no database needed)."""
    from services.canvas_service import CanvasService
    return CanvasService(event_bus)


@pytest.fixture
def editor_service(event_bus: EventBus):
    """Create an EditorService (no database needed)."""
    from services.editor_service import EditorService
    return EditorService(event_bus)


@pytest.fixture
def all_services(
    test_db_path: str,
    event_bus: EventBus,
    project_service,
    story_service,
    chapter_service,
    encyclopedia_service,
    canvas_service,
    editor_service,
) -> Dict[str, Any]:
    """Create all services as a dictionary (matching API server expectations)."""
    return {
        'project': project_service,
        'story': story_service,
        'chapter': chapter_service,
        'encyclopedia': encyclopedia_service,
        'canvas': canvas_service,
        'editor': editor_service,
    }


# =============================================================================
# Sample Data Factories
# =============================================================================

@pytest.fixture
def sample_project(project_service):
    """Create a sample project and return its DTO."""
    return project_service.create_project(
        name="Test Novel",
        description="A test novel for unit testing"
    )


@pytest.fixture
def sample_story(story_service, sample_project):
    """Create a sample story in the sample project."""
    return story_service.create_story(
        project_id=sample_project.id,
        title="Test Story",
        synopsis="A story for testing purposes"
    )


@pytest.fixture
def sample_chapter(chapter_service, sample_story):
    """Create a sample chapter in the sample story."""
    return chapter_service.create_chapter(
        story_id=sample_story.id,
        title="Test Chapter",
        board_x=100,
        board_y=100,
        color="#FFFF88"
    )


@pytest.fixture
def sample_entry(encyclopedia_service, sample_project):
    """Create a sample encyclopedia entry in the sample project."""
    return encyclopedia_service.create_entry(
        project_id=sample_project.id,
        name="Test Character",
        category="Character",
        content="A test character description",
        tags="test, character"
    )
