"""
BlueWriter Event Definitions.

All events that can be emitted by services. Events are dataclasses
that inherit from Event and include relevant data for subscribers.

Events are organized by domain:
- Project events
- Story events (Task 1.3)
- Chapter events (Task 1.4)
- Encyclopedia events (Task 1.5)
- Canvas/Editor events (Task 1.6)
"""
from dataclasses import dataclass
from typing import List

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


__all__ = [
    # Project events
    'ProjectCreated',
    'ProjectUpdated', 
    'ProjectDeleted',
    'ProjectOpened',
]
