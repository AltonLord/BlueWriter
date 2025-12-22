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
    Subclasses should add their specific data fields BEFORE
    inheriting, since timestamp has a default value.
    
    Note: Due to dataclass inheritance rules, child classes
    must either:
    - Define their fields before the parent's default fields
    - Or give all their fields default values
    
    We solve this by setting timestamp in __post_init__.
    
    Example:
        @dataclass
        class ChapterCreated(Event):
            chapter_id: int
            story_id: int
            title: str
    """
    # Using field with init=False so subclasses can have required fields
    timestamp: datetime = field(default=None, init=False)
    
    def __post_init__(self):
        """Set timestamp after initialization."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


# Re-export event types for convenience
from events.events import (
    ProjectCreated,
    ProjectUpdated,
    ProjectDeleted,
    ProjectOpened,
)

__all__ = [
    'Event',
    'ProjectCreated',
    'ProjectUpdated',
    'ProjectDeleted',
    'ProjectOpened',
]
