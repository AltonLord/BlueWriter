"""
Qt Event Adapter for BlueWriter.

Bridges the framework-agnostic EventBus to Qt signals,
ensuring all UI updates happen on the main thread.
"""
from typing import List

from PySide6.QtCore import QObject, Signal, QTimer

from events.event_bus import EventBus
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
    # App events
    AppStateChanged,
    SaveRequested,
    SaveCompleted,
)


class QtEventAdapter(QObject):
    """
    Bridges EventBus to Qt signals.
    
    Subscribes to all event types on the EventBus and emits
    corresponding Qt signals. Uses a QTimer to poll for pending
    events from background threads.
    
    Usage:
        event_bus = EventBus()
        adapter = QtEventAdapter(event_bus, parent=main_window)
        adapter.chapter_created.connect(main_window.on_chapter_created)
    """
    
    # === Project Signals ===
    project_created = Signal(int, str)  # project_id, name
    project_updated = Signal(int, list)  # project_id, fields_changed
    project_deleted = Signal(int)  # project_id
    project_opened = Signal(int)  # project_id
    
    # === Story Signals ===
    story_created = Signal(int, int, str)  # story_id, project_id, title
    story_updated = Signal(int, list)  # story_id, fields_changed
    story_deleted = Signal(int)  # story_id
    story_selected = Signal(int)  # story_id
    story_published = Signal(int, str)  # story_id, status
    story_unpublished = Signal(int)  # story_id
    stories_reordered = Signal(int, list)  # project_id, story_ids
    
    # === Chapter Signals ===
    chapter_created = Signal(int, int, str, int, int, str)  # id, story_id, title, x, y, color
    chapter_updated = Signal(int, list)  # chapter_id, fields_changed
    chapter_deleted = Signal(int, int)  # chapter_id, story_id
    chapter_moved = Signal(int, int, int, int, int)  # id, old_x, old_y, new_x, new_y
    chapter_color_changed = Signal(int, str, str)  # chapter_id, old_color, new_color
    chapter_opened = Signal(int)  # chapter_id
    chapter_closed = Signal(int)  # chapter_id
    
    # === Encyclopedia Signals ===
    entry_created = Signal(int, int, str, str)  # entry_id, project_id, name, category
    entry_updated = Signal(int, list)  # entry_id, fields_changed
    entry_deleted = Signal(int, int)  # entry_id, project_id
    entry_opened = Signal(int)  # entry_id
    entry_closed = Signal(int)  # entry_id
    
    # === Canvas Signals ===
    canvas_panned = Signal(int, float, float, float, float)  # story_id, old_x, old_y, new_x, new_y
    canvas_zoomed = Signal(int, float, float)  # story_id, old_zoom, new_zoom
    
    # === Editor Signals ===
    editor_state_changed = Signal(str, int, bool)  # editor_type, item_id, is_open
    editor_modified_changed = Signal(str, int, bool)  # editor_type, item_id, is_modified
    
    # === App Signals ===
    app_state_changed = Signal(object, object)  # current_project_id, current_story_id (can be None)
    save_requested = Signal(bool)  # save_all
    save_completed = Signal(int, bool, str)  # items_saved, success, error_message
    
    def __init__(self, event_bus: EventBus, parent=None):
        """
        Initialize the Qt event adapter.
        
        Args:
            event_bus: The EventBus to subscribe to
            parent: Qt parent object (typically MainWindow)
        """
        super().__init__(parent)
        self.event_bus = event_bus
        
        # Subscribe to all event types
        self._subscribe_to_events()
        
        # Timer to process pending events from background threads
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_pending_events)
        self._timer.start(50)  # 50ms polling interval
    
    def _subscribe_to_events(self) -> None:
        """Subscribe to all event types on the EventBus."""
        # Project events
        self.event_bus.subscribe(ProjectCreated, self._on_project_created)
        self.event_bus.subscribe(ProjectUpdated, self._on_project_updated)
        self.event_bus.subscribe(ProjectDeleted, self._on_project_deleted)
        self.event_bus.subscribe(ProjectOpened, self._on_project_opened)
        
        # Story events
        self.event_bus.subscribe(StoryCreated, self._on_story_created)
        self.event_bus.subscribe(StoryUpdated, self._on_story_updated)
        self.event_bus.subscribe(StoryDeleted, self._on_story_deleted)
        self.event_bus.subscribe(StorySelected, self._on_story_selected)
        self.event_bus.subscribe(StoryPublished, self._on_story_published)
        self.event_bus.subscribe(StoryUnpublished, self._on_story_unpublished)
        self.event_bus.subscribe(StoriesReordered, self._on_stories_reordered)
        
        # Chapter events
        self.event_bus.subscribe(ChapterCreated, self._on_chapter_created)
        self.event_bus.subscribe(ChapterUpdated, self._on_chapter_updated)
        self.event_bus.subscribe(ChapterDeleted, self._on_chapter_deleted)
        self.event_bus.subscribe(ChapterMoved, self._on_chapter_moved)
        self.event_bus.subscribe(ChapterColorChanged, self._on_chapter_color_changed)
        self.event_bus.subscribe(ChapterOpened, self._on_chapter_opened)
        self.event_bus.subscribe(ChapterClosed, self._on_chapter_closed)
        
        # Encyclopedia events
        self.event_bus.subscribe(EntryCreated, self._on_entry_created)
        self.event_bus.subscribe(EntryUpdated, self._on_entry_updated)
        self.event_bus.subscribe(EntryDeleted, self._on_entry_deleted)
        self.event_bus.subscribe(EntryOpened, self._on_entry_opened)
        self.event_bus.subscribe(EntryClosed, self._on_entry_closed)
        
        # Canvas events
        self.event_bus.subscribe(CanvasPanned, self._on_canvas_panned)
        self.event_bus.subscribe(CanvasZoomed, self._on_canvas_zoomed)
        
        # Editor events
        self.event_bus.subscribe(EditorStateChanged, self._on_editor_state_changed)
        self.event_bus.subscribe(EditorModifiedChanged, self._on_editor_modified_changed)
        
        # App events
        self.event_bus.subscribe(AppStateChanged, self._on_app_state_changed)
        self.event_bus.subscribe(SaveRequested, self._on_save_requested)
        self.event_bus.subscribe(SaveCompleted, self._on_save_completed)
    
    def _process_pending_events(self) -> None:
        """Process pending events from background threads."""
        self.event_bus.process_pending()
    
    def stop(self) -> None:
        """Stop the polling timer."""
        self._timer.stop()
    
    # === Project Event Handlers ===
    
    def _on_project_created(self, event: ProjectCreated) -> None:
        self.project_created.emit(event.project_id, event.name)
    
    def _on_project_updated(self, event: ProjectUpdated) -> None:
        self.project_updated.emit(event.project_id, event.fields_changed)
    
    def _on_project_deleted(self, event: ProjectDeleted) -> None:
        self.project_deleted.emit(event.project_id)
    
    def _on_project_opened(self, event: ProjectOpened) -> None:
        self.project_opened.emit(event.project_id)
    
    # === Story Event Handlers ===
    
    def _on_story_created(self, event: StoryCreated) -> None:
        self.story_created.emit(event.story_id, event.project_id, event.title)
    
    def _on_story_updated(self, event: StoryUpdated) -> None:
        self.story_updated.emit(event.story_id, event.fields_changed)
    
    def _on_story_deleted(self, event: StoryDeleted) -> None:
        self.story_deleted.emit(event.story_id)
    
    def _on_story_selected(self, event: StorySelected) -> None:
        self.story_selected.emit(event.story_id)
    
    def _on_story_published(self, event: StoryPublished) -> None:
        self.story_published.emit(event.story_id, event.status)
    
    def _on_story_unpublished(self, event: StoryUnpublished) -> None:
        self.story_unpublished.emit(event.story_id)
    
    def _on_stories_reordered(self, event: StoriesReordered) -> None:
        self.stories_reordered.emit(event.project_id, event.story_ids)
    
    # === Chapter Event Handlers ===
    
    def _on_chapter_created(self, event: ChapterCreated) -> None:
        self.chapter_created.emit(
            event.chapter_id, event.story_id, event.title,
            event.board_x, event.board_y, event.color
        )
    
    def _on_chapter_updated(self, event: ChapterUpdated) -> None:
        self.chapter_updated.emit(event.chapter_id, event.fields_changed)
    
    def _on_chapter_deleted(self, event: ChapterDeleted) -> None:
        self.chapter_deleted.emit(event.chapter_id, event.story_id)
    
    def _on_chapter_moved(self, event: ChapterMoved) -> None:
        self.chapter_moved.emit(
            event.chapter_id, event.old_x, event.old_y,
            event.new_x, event.new_y
        )
    
    def _on_chapter_color_changed(self, event: ChapterColorChanged) -> None:
        self.chapter_color_changed.emit(
            event.chapter_id, event.old_color, event.new_color
        )
    
    def _on_chapter_opened(self, event: ChapterOpened) -> None:
        self.chapter_opened.emit(event.chapter_id)
    
    def _on_chapter_closed(self, event: ChapterClosed) -> None:
        self.chapter_closed.emit(event.chapter_id)
    
    # === Encyclopedia Event Handlers ===
    
    def _on_entry_created(self, event: EntryCreated) -> None:
        self.entry_created.emit(
            event.entry_id, event.project_id, event.name, event.category
        )
    
    def _on_entry_updated(self, event: EntryUpdated) -> None:
        self.entry_updated.emit(event.entry_id, event.fields_changed)
    
    def _on_entry_deleted(self, event: EntryDeleted) -> None:
        self.entry_deleted.emit(event.entry_id, event.project_id)
    
    def _on_entry_opened(self, event: EntryOpened) -> None:
        self.entry_opened.emit(event.entry_id)
    
    def _on_entry_closed(self, event: EntryClosed) -> None:
        self.entry_closed.emit(event.entry_id)
    
    # === Canvas Event Handlers ===
    
    def _on_canvas_panned(self, event: CanvasPanned) -> None:
        self.canvas_panned.emit(
            event.story_id, event.old_x, event.old_y,
            event.new_x, event.new_y
        )
    
    def _on_canvas_zoomed(self, event: CanvasZoomed) -> None:
        self.canvas_zoomed.emit(event.story_id, event.old_zoom, event.new_zoom)
    
    # === Editor Event Handlers ===
    
    def _on_editor_state_changed(self, event: EditorStateChanged) -> None:
        self.editor_state_changed.emit(
            event.editor_type, event.item_id, event.is_open
        )
    
    def _on_editor_modified_changed(self, event: EditorModifiedChanged) -> None:
        self.editor_modified_changed.emit(
            event.editor_type, event.item_id, event.is_modified
        )
    
    # === App Event Handlers ===
    
    def _on_app_state_changed(self, event: AppStateChanged) -> None:
        self.app_state_changed.emit(
            event.current_project_id, event.current_story_id
        )
    
    def _on_save_requested(self, event: SaveRequested) -> None:
        self.save_requested.emit(event.save_all)
    
    def _on_save_completed(self, event: SaveCompleted) -> None:
        self.save_completed.emit(
            event.items_saved, event.success, event.error_message or ""
        )


__all__ = ['QtEventAdapter']
