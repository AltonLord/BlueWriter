"""
BlueWriter Event System.

This package provides a framework-agnostic event bus for
publishing and subscribing to application events.
"""
from dataclasses import dataclass, field
from datetime import datetime


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
    """
    timestamp: datetime = field(default=None, init=False)
    
    def __post_init__(self):
        """Set timestamp after initialization."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


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
]
