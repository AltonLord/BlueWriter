"""
BlueWriter Event Definitions.

All events that can be emitted by services. Events are dataclasses
that inherit from Event and include relevant data for subscribers.

Events are organized by domain:
- Project events
- Story events
- Chapter events (Task 1.4)
- Encyclopedia events (Task 1.5)
- Canvas/Editor events (Task 1.6)
"""
from dataclasses import dataclass
from typing import List, Optional

from events import Event


# =============================================================================
# Project Events
# =============================================================================

@dataclass
class ProjectCreated(Event):
    """Emitted when a new project is created."""
    project_id: int
    name: str


@dataclass
class ProjectUpdated(Event):
    """Emitted when a project is modified."""
    project_id: int
    fields_changed: List[str]


@dataclass
class ProjectDeleted(Event):
    """Emitted when a project is deleted."""
    project_id: int


@dataclass
class ProjectOpened(Event):
    """Emitted when a project is opened/selected in the UI."""
    project_id: int


# =============================================================================
# Story Events
# =============================================================================

@dataclass
class StoryCreated(Event):
    """Emitted when a new story is created."""
    story_id: int
    project_id: int
    title: str


@dataclass
class StoryUpdated(Event):
    """Emitted when a story is modified."""
    story_id: int
    fields_changed: List[str]


@dataclass
class StoryDeleted(Event):
    """Emitted when a story is deleted."""
    story_id: int


@dataclass
class StorySelected(Event):
    """Emitted when a story is selected in the UI."""
    story_id: int


@dataclass
class StoryPublished(Event):
    """Emitted when a story is published (rough or final)."""
    story_id: int
    status: str  # 'rough_published' or 'final_published'


@dataclass
class StoryUnpublished(Event):
    """Emitted when a story is unpublished (reverted to draft)."""
    story_id: int


@dataclass
class StoriesReordered(Event):
    """Emitted when stories are reordered within a project."""
    project_id: int
    story_ids: List[int]  # New order


__all__ = [
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
]
