"""
Event debugging utilities for BlueWriter.

Provides tools for logging and recording events during development
and testing.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Type

from events import Event
from events.event_bus import EventBus
from events.events import (
    # Import all event types for subscription
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


# All event types for subscription
ALL_EVENT_TYPES: List[Type[Event]] = [
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


class EventLogger:
    """Logs all events to console and/or file for debugging.
    
    Subscribes to all event types and logs them as they occur.
    Useful for debugging event flow during development.
    
    Example:
        event_bus = EventBus()
        logger = EventLogger(event_bus)  # Console only
        
        # Or log to file
        logger = EventLogger(event_bus, log_file="/tmp/events.log")
        
        # Later, stop logging
        logger.stop()
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        log_file: Optional[str] = None,
        console: bool = True,
        include_timestamp: bool = True,
        include_data: bool = True,
    ) -> None:
        """Initialize the event logger.
        
        Args:
            event_bus: EventBus to subscribe to
            log_file: Optional file path to write logs
            console: Whether to print to console (default: True)
            include_timestamp: Include timestamp in log (default: True)
            include_data: Include full event data in log (default: True)
        """
        self.event_bus = event_bus
        self.log_file = Path(log_file) if log_file else None
        self.console = console
        self.include_timestamp = include_timestamp
        self.include_data = include_data
        self._active = False
        self._file_handle = None
        
        self.start()
    
    def start(self) -> None:
        """Start logging events."""
        if self._active:
            return
        
        self._active = True
        
        # Open file if specified
        if self.log_file:
            self._file_handle = open(self.log_file, 'a')
        
        # Subscribe to all event types
        for event_type in ALL_EVENT_TYPES:
            self.event_bus.subscribe(event_type, self._log_event)
    
    def stop(self) -> None:
        """Stop logging events."""
        if not self._active:
            return
        
        self._active = False
        
        # Unsubscribe from all event types
        for event_type in ALL_EVENT_TYPES:
            self.event_bus.unsubscribe(event_type, self._log_event)
        
        # Close file if open
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
    
    def _log_event(self, event: Event) -> None:
        """Log an event to console and/or file.
        
        Args:
            event: The event to log
        """
        if not self._active:
            return
        
        # Build log message
        parts = []
        
        if self.include_timestamp:
            parts.append(f"[{datetime.now().isoformat()}]")
        
        parts.append(f"EVENT: {type(event).__name__}")
        
        if self.include_data:
            # Get event data without timestamp (already shown)
            data = event.to_dict()
            data.pop('timestamp', None)
            data.pop('event_type', None)
            if data:
                parts.append(f"| {json.dumps(data)}")
        
        message = " ".join(parts)
        
        # Output to console
        if self.console:
            print(message)
        
        # Output to file
        if self._file_handle:
            self._file_handle.write(message + "\n")
            self._file_handle.flush()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop logging."""
        self.stop()
        return False


class EventRecorder:
    """Records events for inspection and testing.
    
    Useful for unit tests to verify correct events are emitted,
    or for debugging to see the sequence of events.
    
    Example:
        event_bus = EventBus()
        recorder = EventRecorder(event_bus)
        recorder.start_recording()
        
        # ... do some operations ...
        
        recorder.stop_recording()
        
        # Inspect recorded events
        all_events = recorder.get_events()
        chapter_events = recorder.get_events(ChapterCreated)
        
        # Or use as context manager
        with EventRecorder(event_bus, auto_start=True) as recorder:
            # ... do operations ...
            events = recorder.get_events()
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        auto_start: bool = False,
    ) -> None:
        """Initialize the event recorder.
        
        Args:
            event_bus: EventBus to subscribe to
            auto_start: Start recording immediately (default: False)
        """
        self.event_bus = event_bus
        self.events: List[Event] = []
        self._recording = False
        
        if auto_start:
            self.start_recording()
    
    def start_recording(self) -> None:
        """Start recording events."""
        if self._recording:
            return
        
        self._recording = True
        
        # Subscribe to all event types
        for event_type in ALL_EVENT_TYPES:
            self.event_bus.subscribe(event_type, self._record_event)
    
    def stop_recording(self) -> None:
        """Stop recording events."""
        if not self._recording:
            return
        
        self._recording = False
        
        # Unsubscribe from all event types
        for event_type in ALL_EVENT_TYPES:
            self.event_bus.unsubscribe(event_type, self._record_event)
    
    def _record_event(self, event: Event) -> None:
        """Record an event.
        
        Args:
            event: The event to record
        """
        if self._recording:
            self.events.append(event)
    
    def get_events(self, event_type: Optional[Type[Event]] = None) -> List[Event]:
        """Get recorded events, optionally filtered by type.
        
        Args:
            event_type: If provided, only return events of this type
            
        Returns:
            List of recorded events
        """
        if event_type is None:
            return list(self.events)
        return [e for e in self.events if isinstance(e, event_type)]
    
    def get_event_types(self) -> List[str]:
        """Get list of recorded event type names.
        
        Returns:
            List of event type names in order recorded
        """
        return [type(e).__name__ for e in self.events]
    
    def count(self, event_type: Optional[Type[Event]] = None) -> int:
        """Count recorded events, optionally by type.
        
        Args:
            event_type: If provided, only count events of this type
            
        Returns:
            Number of matching events
        """
        return len(self.get_events(event_type))
    
    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()
    
    def is_recording(self) -> bool:
        """Check if currently recording.
        
        Returns:
            True if recording, False otherwise
        """
        return self._recording
    
    def __enter__(self):
        """Context manager entry - start recording."""
        self.start_recording()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop recording."""
        self.stop_recording()
        return False
    
    def __len__(self) -> int:
        """Return number of recorded events."""
        return len(self.events)


__all__ = ['EventLogger', 'EventRecorder', 'ALL_EVENT_TYPES']
