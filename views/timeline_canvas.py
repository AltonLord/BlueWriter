"""
Timeline canvas for BlueWriter.
Displays a unified project canvas with story overlays and chapter sticky notes.
"""
import json
import math

from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtGui import (
    QPainter, QBrush, QColor, QPen, QFont, QMouseEvent, QAction,
    QPainterPath
)
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, Signal


class TimelineCanvas(QWidget):
    """Canvas widget for displaying a unified project canvas with story overlays."""

    # Signal to request new chapter at position
    new_chapter_requested = Signal(float, float)  # canvas x, y position
    # Signal emitted when a story outline is updated in edit mode
    story_outline_updated = Signal(int, str)  # story_id, bounding_data JSON
    # Signal emitted when outline edit mode changes
    outline_edit_mode_changed = Signal(bool)  # True = editing, False = normal

    def __init__(self, parent=None) -> None:
        """Initialize the timeline canvas."""
        super().__init__(parent)
        self.setMinimumSize(800, 600)

        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(250, 250, 245))
        self.setPalette(palette)

        # Zoom and pan properties
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.is_panning = False
        self.last_mouse_pos = QPoint()
        self.last_context_pos = QPoint()

        # Unified canvas data
        self._stories = []       # List of StoryDTO
        self._chapters = []      # List of ChapterDTO
        self._chapter_map = {}   # chapter_id -> ChapterDTO for quick lookup
        self._project_id = None

        # Outline edit mode
        self._edit_mode_story_id = None  # story_id being edited, or None

        # Enable keyboard focus for Escape key handling
        self.setFocusPolicy(Qt.StrongFocus)

    # === Unified Canvas Loading ===

    def load_project(self, project_id, chapters, stories):
        """Load all chapters and stories for a project onto the canvas.

        Args:
            project_id: The project ID
            chapters: List of ChapterDTO objects
            stories: List of StoryDTO objects
        """
        self._project_id = project_id
        self.set_stories(stories)
        self.set_chapters(chapters)
        self.update()

    def set_stories(self, stories):
        """Set the story overlay data for canvas rendering.

        Args:
            stories: List of StoryDTO objects
        """
        self._stories = list(stories)
        self.update()

    def set_chapters(self, chapters):
        """Set the chapter data and rebuild the lookup map.

        Args:
            chapters: List of ChapterDTO objects
        """
        self._chapters = list(chapters)
        self._chapter_map = {ch.id: ch for ch in self._chapters}
        self.update()

    # === Outline Edit Mode ===

    def enter_outline_edit_mode(self, story_id):
        """Enter edit mode for a specific story's outline.

        Box mode: Shows the story's bounding box for editing.
        String mode: Highlights chapters for path definition.
        Pressing Escape exits edit mode.

        Args:
            story_id: The story ID to edit
        """
        self._edit_mode_story_id = story_id
        self.outline_edit_mode_changed.emit(True)
        self.setFocus()
        self.update()

    def exit_outline_edit_mode(self):
        """Exit outline edit mode and emit story_outline_updated if applicable."""
        if self._edit_mode_story_id is not None:
            # Find the story being edited and emit its current bounding_data
            for story in self._stories:
                if story.id == self._edit_mode_story_id:
                    if story.bounding_data:
                        self.story_outline_updated.emit(story.id, story.bounding_data)
                    break
            self._edit_mode_story_id = None
            self.outline_edit_mode_changed.emit(False)
            self.update()

    def frame_story(self, story_dto, chapters):
        """Pan and zoom canvas to frame a specific story's chapters in view.

        Args:
            story_dto: The StoryDTO to frame
            chapters: List of ChapterDTO for this story
        """
        if not chapters:
            return

        # Calculate bounding box of the story's chapters
        min_x = min(ch.board_x for ch in chapters)
        min_y = min(ch.board_y for ch in chapters)
        max_x = max(ch.board_x + 160 for ch in chapters)  # sticky note width
        max_y = max(ch.board_y + 100 for ch in chapters)   # sticky note height

        # Add padding
        padding = 80
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        # Calculate zoom to fit
        content_width = max_x - min_x
        content_height = max_y - min_y

        if content_width <= 0 or content_height <= 0:
            return

        zoom_x = self.width() / content_width
        zoom_y = self.height() / content_height
        self.zoom_level = min(zoom_x, zoom_y, 2.0)  # Cap at 2x
        self.zoom_level = max(self.zoom_level, 0.2)

        # Center the content
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.pan_x = self.width() / 2 - center_x * self.zoom_level
        self.pan_y = self.height() / 2 - center_y * self.zoom_level

        self.update_sticky_note_positions()
        self.update()

    # === Coordinate Conversion ===

    def canvas_to_screen(self, canvas_x: float, canvas_y: float) -> tuple:
        """Convert canvas coordinates to screen coordinates."""
        screen_x = canvas_x * self.zoom_level + self.pan_x
        screen_y = canvas_y * self.zoom_level + self.pan_y
        return (screen_x, screen_y)

    def screen_to_canvas(self, screen_x: float, screen_y: float) -> tuple:
        """Convert screen coordinates to canvas coordinates."""
        canvas_x = (screen_x - self.pan_x) / self.zoom_level
        canvas_y = (screen_y - self.pan_y) / self.zoom_level
        return (canvas_x, canvas_y)

    def update_sticky_note_positions(self) -> None:
        """Reposition all sticky notes based on current pan/zoom."""
        for child in self.children():
            if hasattr(child, 'canvas_x') and hasattr(child, 'canvas_y'):
                screen_x, screen_y = self.canvas_to_screen(child.canvas_x, child.canvas_y)
                child.move(int(screen_x), int(screen_y))

    # === Context Menu ===

    def show_context_menu(self, pos: QPoint) -> None:
        """Show context menu on right-click."""
        self.last_context_pos = pos

        menu = QMenu(self)
        new_chapter_action = QAction("New Chapter Here", self)
        new_chapter_action.triggered.connect(self.request_new_chapter)
        menu.addAction(new_chapter_action)

        menu.exec(self.mapToGlobal(pos))

    def request_new_chapter(self) -> None:
        """Emit signal to create new chapter at right-click position (in canvas coords)."""
        canvas_x, canvas_y = self.screen_to_canvas(
            self.last_context_pos.x(),
            self.last_context_pos.y()
        )
        self.new_chapter_requested.emit(canvas_x, canvas_y)

    # === Key Events ===

    def keyPressEvent(self, event) -> None:
        """Handle key press events. Escape exits outline edit mode."""
        if event.key() == Qt.Key_Escape and self._edit_mode_story_id is not None:
            self.exit_outline_edit_mode()
            event.accept()
            return
        super().keyPressEvent(event)

    # === Paint Event ===

    def paintEvent(self, event) -> None:
        """Handle painting of the canvas."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply transformations
        painter.translate(self.pan_x, self.pan_y)
        painter.scale(self.zoom_level, self.zoom_level)

        # Draw background elements
        self.draw_sine_wave_background(painter)
        self.draw_timeline_elements(painter)

        # Draw story overlays (beneath sticky notes which are child widgets)
        self.draw_story_overlays(painter)

    # === Mouse Events for Panning ===

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for panning (on empty canvas only)."""
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            # Only pan if clicking on empty canvas, not on a sticky note
            child = self.childAt(event.position().toPoint())
            if child is None:
                self.is_panning = True
                self.last_mouse_pos = event.position().toPoint()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse movement for panning."""
        if self.is_panning:
            delta = event.position().toPoint() - self.last_mouse_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_mouse_pos = event.position().toPoint()

            # Reposition all sticky notes
            self.update_sticky_note_positions()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release to stop panning."""
        if event.button() in (Qt.LeftButton, Qt.MiddleButton) and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # === Zoom Events ===

    def wheelEvent(self, event) -> None:
        """Handle zoom with mouse wheel."""
        # Get mouse position before zoom
        mouse_pos = event.position()
        old_canvas_x, old_canvas_y = self.screen_to_canvas(mouse_pos.x(), mouse_pos.y())

        # Calculate zoom
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.zoom_level *= zoom_factor
        else:
            self.zoom_level /= zoom_factor

        # Clamp zoom level
        self.zoom_level = max(0.2, min(self.zoom_level, 5.0))

        # Adjust pan to keep mouse position fixed (zoom toward cursor)
        new_screen_x, new_screen_y = self.canvas_to_screen(old_canvas_x, old_canvas_y)
        self.pan_x += mouse_pos.x() - new_screen_x
        self.pan_y += mouse_pos.y() - new_screen_y

        # Reposition sticky notes and redraw
        self.update_sticky_note_positions()
        self.update()
        event.accept()

    def zoom_in(self) -> None:
        """Zoom in on the canvas."""
        self.zoom_level *= 1.2
        self.zoom_level = min(self.zoom_level, 5.0)
        self.update_sticky_note_positions()
        self.update()

    def zoom_out(self) -> None:
        """Zoom out on the canvas."""
        self.zoom_level /= 1.2
        self.zoom_level = max(self.zoom_level, 0.2)
        self.update_sticky_note_positions()
        self.update()

    def reset_zoom(self) -> None:
        """Reset zoom to 100% and center."""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_sticky_note_positions()
        self.update()

    # === Drawing Functions ===

    def draw_sine_wave_background(self, painter: QPainter) -> None:
        """Draw a sine wave pattern as background guide."""
        pen = QPen(QColor(210, 210, 200), 2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # Draw a prominent center sine wave
        amplitude = 80
        wavelength = 400
        center_y = 300

        # Draw the wave across a wide area
        points = []
        for x in range(-200, 3000, 8):
            y = center_y + amplitude * math.sin(2 * math.pi * x / wavelength)
            points.append((x, y))

        for i in range(len(points) - 1):
            painter.drawLine(
                int(points[i][0]), int(points[i][1]),
                int(points[i+1][0]), int(points[i+1][1])
            )

        # Draw some horizontal guide lines
        pen.setStyle(Qt.DotLine)
        pen.setColor(QColor(220, 220, 215))
        painter.setPen(pen)

        for y in range(100, 600, 100):
            painter.drawLine(-200, y, 3000, y)

    def draw_timeline_elements(self, painter: QPainter) -> None:
        """Draw timeline markers and labels."""
        # Draw main horizontal axis
        pen = QPen(QColor(180, 180, 170), 1)
        painter.setPen(pen)
        painter.drawLine(-200, 300, 3000, 300)

        # Draw vertical markers
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(150, 150, 140)))

        for x in range(0, 2800, 200):
            painter.drawLine(x, 290, x, 310)
            painter.drawText(x - 20, 330, f"{x // 200}")

    def draw_story_overlays(self, painter: QPainter) -> None:
        """Draw all story boxes and strings beneath sticky notes."""
        for story in self._stories:
            if story.representation_type == 'box':
                self._draw_story_box(painter, story)
            elif story.representation_type == 'string':
                self._draw_story_string(painter, story)

    def _draw_story_box(self, painter: QPainter, story) -> None:
        """Draw semi-transparent filled rectangle with colored border."""
        if not story.bounding_data:
            return
        try:
            data = json.loads(story.bounding_data)
        except (json.JSONDecodeError, TypeError):
            return

        x1 = data.get('x1', 0)
        y1 = data.get('y1', 0)
        x2 = data.get('x2', 0)
        y2 = data.get('y2', 0)
        rect = QRectF(x1, y1, x2 - x1, y2 - y1)

        is_editing = (self._edit_mode_story_id == story.id)

        # Fill: very light tint of outline_color at ~15% opacity
        fill_color = QColor(story.outline_color or "#4A90D9")
        fill_color.setAlpha(50 if is_editing else 38)
        painter.fillRect(rect, fill_color)

        # Border
        border_color = QColor(story.outline_color or "#4A90D9")
        line_width = 3 if is_editing else 2
        pen = QPen(border_color, line_width, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        # Title label top-left
        painter.setPen(QPen(border_color))
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(int(x1) + 8, int(y1) + 20, story.title)

    def _draw_story_string(self, painter: QPainter, story) -> None:
        """Draw red yarn path connecting chapters in order.

        Yarn effect: Two bezier paths offset by 2px with different opacity red
        to create a two-strand rope illusion. No image textures.
        """
        if not story.bounding_data:
            return
        try:
            data = json.loads(story.bounding_data)
        except (json.JSONDecodeError, TypeError):
            return

        chapter_ids = data.get('chapter_ids', [])

        # Get chapter center positions in order
        points = []
        for cid in chapter_ids:
            chapter = self._chapter_map.get(cid)
            if chapter:
                # Center of sticky note (160x100 size)
                cx = chapter.board_x + 80
                cy = chapter.board_y + 50
                points.append(QPointF(cx, cy))

        if len(points) < 2:
            return

        is_editing = (self._edit_mode_story_id == story.id)

        # Yarn strand 1 (main, darker red)
        yarn_color_1 = QColor(220, 30, 30, 200 if is_editing else 160)
        # Yarn strand 2 (offset, lighter red — gives twisted look)
        yarn_color_2 = QColor(255, 80, 80, 150 if is_editing else 100)

        line_width = 4 if is_editing else 3

        path = QPainterPath(points[0])
        for i in range(1, len(points)):
            # Bezier curve: control point is midpoint offset slightly upward
            mid_x = (points[i-1].x() + points[i].x()) / 2
            mid_y = (points[i-1].y() + points[i].y()) / 2 - 20
            path.quadTo(QPointF(mid_x, mid_y), points[i])

        # Draw strand 2 (offset by 2px)
        painter.save()
        painter.translate(2, 2)
        painter.setPen(QPen(yarn_color_2, line_width - 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        painter.restore()

        # Draw strand 1
        painter.setPen(QPen(yarn_color_1, line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Draw story title near first point
        painter.setPen(QPen(QColor(180, 20, 20)))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(int(points[0].x()) + 10, int(points[0].y()) - 10, story.title)

    def update_color(self):
        """Update the note's color display (called from main_window)."""
        self.update()
