"""
BlueWriter Event Definitions.

All events that can be emitted by services. Events are dataclasses
that inherit from Event and include relevant data for subscribers.

Events are organized by domain:
- Project events
- Story events
- Chapter events
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


# =============================================================================
# Chapter Events
# =============================================================================

@dataclass
class ChapterCreated(Event):
    """Emitted when a new chapter is created."""
    chapter_id: int
    story_id: int
    title: str
    board_x: float
    board_y: float


@dataclass
class ChapterUpdated(Event):
    """Emitted when a chapter is modified."""
    chapter_id: int
    fields_changed: List[str]


@dataclass
class ChapterDeleted(Event):
    """Emitted when a chapter is deleted."""
    chapter_id: int
    story_id: int


@dataclass
class ChapterMoved(Event):
    """Emitted when a chapter's sticky note is moved on the canvas."""
    chapter_id: int
    old_x: float
    old_y: float
    new_x: float
    new_y: float


@dataclass
class ChapterColorChanged(Event):
    """Emitted when a chapter's sticky note color changes."""
    chapter_id: int
    old_color: str
    new_color: str


@dataclass
class ChapterOpened(Event):
    """Emitted when a chapter is opened in the editor."""
    chapter_id: int


@dataclass
class ChapterClosed(Event):
    """Emitted when a chapter editor is closed."""
    chapter_id: int


# =============================================================================
# Encyclopedia Events
# =============================================================================

@dataclass
class EntryCreated(Event):
    """Emitted when a new encyclopedia entry is created."""
    entry_id: int
    project_id: int
    name: str
    category: str


@dataclass
class EntryUpdated(Event):
    """Emitted when an encyclopedia entry is modified."""
    entry_id: int
    fields_changed: List[str]


@dataclass
class EntryDeleted(Event):
    """Emitted when an encyclopedia entry is deleted."""
    entry_id: int
    project_id: int


@dataclass
class EntryOpened(Event):
    """Emitted when an encyclopedia entry is opened in the editor."""
    entry_id: int


@dataclass
class EntryClosed(Event):
    """Emitted when an encyclopedia entry editor is closed."""
    entry_id: int


# =============================================================================
# Canvas Events
# =============================================================================

@dataclass
class CanvasPanned(Event):
    """Emitted when the canvas is panned."""
    story_id: int
    old_x: float
    old_y: float
    new_x: float
    new_y: float


@dataclass
class CanvasZoomed(Event):
    """Emitted when the canvas zoom level changes."""
    story_id: int
    old_zoom: float
    new_zoom: float


# =============================================================================
# Editor Events
# =============================================================================

@dataclass
class EditorStateChanged(Event):
    """Emitted when an editor's open/close state changes."""
    editor_type: str  # "chapter" or "encyclopedia"
    item_id: int
    is_open: bool


@dataclass
class EditorModifiedChanged(Event):
    """Emitted when an editor's modified (dirty) state changes."""
    editor_type: str
    item_id: int
    is_modified: bool


# =============================================================================
# Application Events
# =============================================================================

@dataclass
class AppStateChanged(Event):
    """Emitted when application state changes (project/story selection)."""
    current_project_id: Optional[int]
    current_story_id: Optional[int]


@dataclass
class SaveRequested(Event):
    """Emitted when a save operation is requested."""
    save_all: bool = False  # If True, save all modified editors


@dataclass
class SaveCompleted(Event):
    """Emitted when a save operation completes."""
    items_saved: int
    success: bool
    error_message: Optional[str] = None


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
