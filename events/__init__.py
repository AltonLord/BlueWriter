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
    
    Example:
        @dataclass
        class ChapterCreated(Event):
            chapter_id: int
            story_id: int
            title: str
    """
    timestamp: datetime = field(default_factory=datetime.now)


__all__ = ['Event']
