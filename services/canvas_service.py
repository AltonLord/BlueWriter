"""
Canvas service for BlueWriter.

Manages canvas viewport state (pan/zoom) for each story.
This is a stateful service - state is stored in memory, not database.
Emits events for state changes that UI can subscribe to.
"""
from dataclasses import dataclass
from typing import Dict, Optional

from events.event_bus import EventBus
from events.events import CanvasPanned, CanvasZoomed


# Default canvas view settings
DEFAULT_PAN_X = 0.0
DEFAULT_PAN_Y = 0.0
DEFAULT_ZOOM = 1.0
MIN_ZOOM = 0.1
MAX_ZOOM = 3.0


@dataclass
class CanvasViewDTO:
    """Data transfer object for canvas view state.
    
    Represents the current viewport state for a story's canvas.
    """
    pan_x: float
    pan_y: float
    zoom: float


class CanvasService:
    """Service for managing canvas viewport state.
    
    Tracks pan and zoom state per story. State is stored in memory
    and does not persist to database - it resets when the app restarts.
    
    Note: Unlike other services, this does not inherit from BaseService
    since it doesn't need database access.
    
    Example:
        event_bus = EventBus()
        service = CanvasService(event_bus)
        
        # Get current view
        view = service.get_view(story_id=1)
        
        # Pan the canvas
        service.set_pan(story_id=1, x=500, y=300)
        
        # Zoom in
        service.set_zoom(story_id=1, zoom=1.5)
    """
    
    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the canvas service.
        
        Args:
            event_bus: EventBus for publishing events
        """
        self.event_bus = event_bus
        self._views: Dict[int, CanvasViewDTO] = {}
    
    def _get_or_create_view(self, story_id: int) -> CanvasViewDTO:
        """Get existing view or create default.
        
        Args:
            story_id: The story's database ID
            
        Returns:
            CanvasViewDTO for the story
        """
        if story_id not in self._views:
            self._views[story_id] = CanvasViewDTO(
                pan_x=DEFAULT_PAN_X,
                pan_y=DEFAULT_PAN_Y,
                zoom=DEFAULT_ZOOM,
            )
        return self._views[story_id]
    
    def get_view(self, story_id: int) -> CanvasViewDTO:
        """Get current canvas view state for a story.
        
        Args:
            story_id: The story's database ID
            
        Returns:
            CanvasViewDTO with current pan/zoom state
        """
        view = self._get_or_create_view(story_id)
        # Return a copy to prevent external modification
        return CanvasViewDTO(
            pan_x=view.pan_x,
            pan_y=view.pan_y,
            zoom=view.zoom,
        )
    
    def set_pan(self, story_id: int, x: float, y: float) -> CanvasViewDTO:
        """Set canvas pan position.
        
        Args:
            story_id: The story's database ID
            x: New X pan position
            y: New Y pan position
            
        Returns:
            Updated CanvasViewDTO
        """
        view = self._get_or_create_view(story_id)
        old_x, old_y = view.pan_x, view.pan_y
        
        view.pan_x = x
        view.pan_y = y
        
        # Emit event
        self.event_bus.publish(CanvasPanned(
            story_id=story_id,
            old_x=old_x,
            old_y=old_y,
            new_x=x,
            new_y=y,
        ))
        
        return self.get_view(story_id)
    
    def set_zoom(self, story_id: int, zoom: float) -> CanvasViewDTO:
        """Set canvas zoom level.
        
        Zoom is clamped to MIN_ZOOM..MAX_ZOOM range.
        
        Args:
            story_id: The story's database ID
            zoom: New zoom level (1.0 = 100%)
            
        Returns:
            Updated CanvasViewDTO
        """
        view = self._get_or_create_view(story_id)
        old_zoom = view.zoom
        
        # Clamp zoom to valid range
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        view.zoom = new_zoom
        
        # Emit event
        self.event_bus.publish(CanvasZoomed(
            story_id=story_id,
            old_zoom=old_zoom,
            new_zoom=new_zoom,
        ))
        
        return self.get_view(story_id)
    
    def focus_chapter(
        self,
        story_id: int,
        chapter_x: float,
        chapter_y: float,
    ) -> CanvasViewDTO:
        """Pan canvas to center on a chapter position.
        
        This is a convenience method that calculates the pan
        needed to center a chapter in the viewport.
        
        Args:
            story_id: The story's database ID
            chapter_x: Chapter's board_x position
            chapter_y: Chapter's board_y position
            
        Returns:
            Updated CanvasViewDTO
        """
        # Center the canvas on the chapter
        # The pan position represents the top-left of the viewport,
        # so we offset by half the viewport size (assuming ~800x600 default)
        # This is a simple implementation - the UI can override with actual viewport size
        return self.set_pan(story_id, chapter_x - 400, chapter_y - 300)
    
    def fit_all(
        self,
        story_id: int,
        chapter_positions: Optional[list] = None,
    ) -> CanvasViewDTO:
        """Fit all chapters in view.
        
        Calculates zoom and pan to show all chapters.
        If no positions provided, resets to default view.
        
        Args:
            story_id: The story's database ID
            chapter_positions: List of (x, y) tuples for chapters
            
        Returns:
            Updated CanvasViewDTO
        """
        if not chapter_positions:
            # Reset to default view
            self.set_zoom(story_id, DEFAULT_ZOOM)
            return self.set_pan(story_id, DEFAULT_PAN_X, DEFAULT_PAN_Y)
        
        # Calculate bounding box
        min_x = min(pos[0] for pos in chapter_positions)
        max_x = max(pos[0] for pos in chapter_positions)
        min_y = min(pos[1] for pos in chapter_positions)
        max_y = max(pos[1] for pos in chapter_positions)
        
        # Add padding (sticky note size ~150x100)
        padding = 100
        min_x -= padding
        min_y -= padding
        max_x += padding + 150
        max_y += padding + 100
        
        # Calculate required zoom to fit (assuming 800x600 viewport)
        viewport_width = 800
        viewport_height = 600
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        zoom_x = viewport_width / content_width if content_width > 0 else 1.0
        zoom_y = viewport_height / content_height if content_height > 0 else 1.0
        zoom = min(zoom_x, zoom_y, MAX_ZOOM)
        zoom = max(zoom, MIN_ZOOM)
        
        # Set zoom and pan to top-left of bounding box
        self.set_zoom(story_id, zoom)
        return self.set_pan(story_id, min_x, min_y)
    
    def reset_view(self, story_id: int) -> CanvasViewDTO:
        """Reset canvas view to defaults.
        
        Args:
            story_id: The story's database ID
            
        Returns:
            Reset CanvasViewDTO
        """
        self.set_zoom(story_id, DEFAULT_ZOOM)
        return self.set_pan(story_id, DEFAULT_PAN_X, DEFAULT_PAN_Y)
    
    def clear_story(self, story_id: int) -> None:
        """Clear stored view state for a story.
        
        Call this when a story is closed or deleted.
        
        Args:
            story_id: The story's database ID
        """
        if story_id in self._views:
            del self._views[story_id]
    
    def clear_all(self) -> None:
        """Clear all stored view states.
        
        Useful for testing or resetting state.
        """
        self._views.clear()
