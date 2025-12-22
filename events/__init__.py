"""
BlueWriter Event System.

This package provides a framework-agnostic event bus for
publishing and subscribing to application events.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from typing import Any, Dict


@dataclass
class Event:
    """Base class for all events.
    
    All events automatically get a timestamp when created.
    Subclasses should add their specific data fields.
    
    Note: Due to dataclass inheritance rules, we use
    field(default=None, init=False) for timestamp so that
    child classes can have required fields.
    
    Example:
        @dataclass
        class ChapterCreated(Event):
            chapter_id: int
            story_id: int
            title: str
        
        event = ChapterCreated(chapter_id=1, story_id=2, title="Intro")
        print(event.to_json())
    """
    timestamp: datetime = field(default=None, init=False)
    
    def __post_init__(self):
        """Set timestamp after initialization."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization.
        
        Returns:
            Dictionary with all event fields plus event_type
        """
        d = asdict(self)
        # Convert timestamp to ISO format string
        if self.timestamp:
            d['timestamp'] = self.timestamp.isoformat()
        # Add event type name
        d['event_type'] = self.__class__.__name__
        return d
    
    def to_json(self) -> str:
        """Convert event to JSON string.
        
        Returns:
            JSON string representation of the event
        """
        return json.dumps(self.to_dict(), default=str)


# Re-export event types for convenience
from events.events import (
    # Project events
    ProjectCreated,
    ProjectUpdated,
    ProjectDeleted,
    ProjectOpened,
    # Story events
    StoryCreated,
    StoryUpdated,
    StoryDeleted,
    StorySelected,
    StoryPublished,
    StoryUnpublished,
    StoriesReordered,
    # Chapter events
    ChapterCreated,
    ChapterUpdated,
    ChapterDeleted,
    ChapterMoved,
    ChapterColorChanged,
    ChapterOpened,
    ChapterClosed,
    # Encyclopedia events
    EntryCreated,
    EntryUpdated,
    EntryDeleted,
    EntryOpened,
    EntryClosed,
    # Canvas events
    CanvasPanned,
    CanvasZoomed,
    # Editor events
    EditorStateChanged,
    EditorModifiedChanged,
    # Application events
    AppStateChanged,
    SaveRequested,
    SaveCompleted,
)

__all__ = [
    'Event',
    # Project events
    'ProjectCreated',
    'ProjectUpdated',
    'ProjectDeleted',
    'ProjectOpened',
    # Story events
    'StoryCreated',
    'StoryUpdated',
    'StoryDeleted',
    'StorySelected',
    'StoryPublished',
    'StoryUnpublished',
    'StoriesReordered',
    # Chapter events
    'ChapterCreated',
    'ChapterUpdated',
    'ChapterDeleted',
    'ChapterMoved',
    'ChapterColorChanged',
    'ChapterOpened',
    'ChapterClosed',
    # Encyclopedia events
    'EntryCreated',
    'EntryUpdated',
    'EntryDeleted',
    'EntryOpened',
    'EntryClosed',
    # Canvas events
    'CanvasPanned',
    'CanvasZoomed',
    # Editor events
    'EditorStateChanged',
    'EditorModifiedChanged',
    # Application events
    'AppStateChanged',
    'SaveRequested',
    'SaveCompleted',
]
