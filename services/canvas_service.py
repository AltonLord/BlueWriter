"""
Canvas service for BlueWriter.

Manages canvas viewport state (pan/zoom) per project.
This is a stateful service - state is stored in memory, not database.
Emits events for state changes that UI can subscribe to.
"""
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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

    Represents the current viewport state for a project's canvas.
    """
    pan_x: float
    pan_y: float
    zoom: float


class CanvasService:
    """Service for managing canvas viewport state.

    Tracks pan and zoom state per project. State is stored in memory
    and does not persist to database - it resets when the app restarts.

    Note: Unlike other services, this does not inherit from BaseService
    since it doesn't need database access.

    The key parameter is called context_id and can represent either a
    project_id (unified canvas) or story_id (legacy API compatibility).
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._views: Dict[int, CanvasViewDTO] = {}

    def _get_or_create_view(self, context_id: int) -> CanvasViewDTO:
        """Get existing view or create default."""
        if context_id not in self._views:
            self._views[context_id] = CanvasViewDTO(
                pan_x=DEFAULT_PAN_X,
                pan_y=DEFAULT_PAN_Y,
                zoom=DEFAULT_ZOOM,
            )
        return self._views[context_id]

    def get_view(self, story_id: int) -> CanvasViewDTO:
        """Get current canvas view state.

        Args:
            story_id: Context ID (project_id or story_id for backward compat)

        Returns:
            CanvasViewDTO with current pan/zoom state
        """
        view = self._get_or_create_view(story_id)
        return CanvasViewDTO(
            pan_x=view.pan_x,
            pan_y=view.pan_y,
            zoom=view.zoom,
        )

    def set_pan(self, story_id: int, x: float, y: float) -> CanvasViewDTO:
        """Set canvas pan position.

        Args:
            story_id: Context ID (project_id or story_id for backward compat)
            x: New X pan position
            y: New Y pan position

        Returns:
            Updated CanvasViewDTO
        """
        view = self._get_or_create_view(story_id)
        old_x, old_y = view.pan_x, view.pan_y

        view.pan_x = x
        view.pan_y = y

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
            story_id: Context ID (project_id or story_id for backward compat)
            zoom: New zoom level (1.0 = 100%)

        Returns:
            Updated CanvasViewDTO
        """
        view = self._get_or_create_view(story_id)
        old_zoom = view.zoom

        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        view.zoom = new_zoom

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
        """Pan canvas to center on a chapter position."""
        return self.set_pan(story_id, chapter_x - 400, chapter_y - 300)

    def frame_story(
        self,
        project_id: int,
        bounding_data: Optional[str],
        chapter_positions: List[Tuple[float, float]],
        viewport_width: int = 800,
        viewport_height: int = 600,
    ) -> CanvasViewDTO:
        """Pan and zoom canvas to frame a specific story's chapters.

        Called when user double-clicks a story card.
        Uses bounding_data if available (box type), otherwise calculates
        from chapter positions.

        Args:
            project_id: The project's database ID
            bounding_data: JSON string with bounding box or chapter_ids
            chapter_positions: List of (x, y) tuples for chapters in the story
            viewport_width: Current viewport width
            viewport_height: Current viewport height

        Returns:
            Updated CanvasViewDTO
        """
        min_x = min_y = max_x = max_y = None

        # Try to use bounding_data for box type
        if bounding_data:
            try:
                data = json.loads(bounding_data)
                if "x1" in data:
                    min_x = data["x1"]
                    min_y = data["y1"]
                    max_x = data["x2"]
                    max_y = data["y2"]
            except (json.JSONDecodeError, KeyError):
                pass

        # Fall back to chapter positions
        if min_x is None and chapter_positions:
            padding = 80
            min_x = min(p[0] for p in chapter_positions) - padding
            min_y = min(p[1] for p in chapter_positions) - padding
            max_x = max(p[0] for p in chapter_positions) + 150 + padding
            max_y = max(p[1] for p in chapter_positions) + 100 + padding

        if min_x is None:
            return self.reset_view(project_id)

        content_width = max_x - min_x
        content_height = max_y - min_y

        zoom_x = viewport_width / content_width if content_width > 0 else 1.0
        zoom_y = viewport_height / content_height if content_height > 0 else 1.0
        zoom = min(zoom_x, zoom_y, MAX_ZOOM)
        zoom = max(zoom, MIN_ZOOM)

        self.set_zoom(project_id, zoom)
        return self.set_pan(project_id, min_x, min_y)

    def fit_all(
        self,
        story_id: int,
        chapter_positions: Optional[list] = None,
    ) -> CanvasViewDTO:
        """Fit all chapters in view."""
        if not chapter_positions:
            self.set_zoom(story_id, DEFAULT_ZOOM)
            return self.set_pan(story_id, DEFAULT_PAN_X, DEFAULT_PAN_Y)

        min_x = min(pos[0] for pos in chapter_positions)
        max_x = max(pos[0] for pos in chapter_positions)
        min_y = min(pos[1] for pos in chapter_positions)
        max_y = max(pos[1] for pos in chapter_positions)

        padding = 100
        min_x -= padding
        min_y -= padding
        max_x += padding + 150
        max_y += padding + 100

        viewport_width = 800
        viewport_height = 600
        content_width = max_x - min_x
        content_height = max_y - min_y

        zoom_x = viewport_width / content_width if content_width > 0 else 1.0
        zoom_y = viewport_height / content_height if content_height > 0 else 1.0
        zoom = min(zoom_x, zoom_y, MAX_ZOOM)
        zoom = max(zoom, MIN_ZOOM)

        self.set_zoom(story_id, zoom)
        return self.set_pan(story_id, min_x, min_y)

    def reset_view(self, story_id: int) -> CanvasViewDTO:
        """Reset canvas view to defaults."""
        self.set_zoom(story_id, DEFAULT_ZOOM)
        return self.set_pan(story_id, DEFAULT_PAN_X, DEFAULT_PAN_Y)

    def clear_story(self, story_id: int) -> None:
        """Clear stored view state for a context."""
        if story_id in self._views:
            del self._views[story_id]

    def clear_all(self) -> None:
        """Clear all stored view states."""
        self._views.clear()
