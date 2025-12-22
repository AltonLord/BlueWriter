"""
Timeline canvas for BlueWriter.
Displays a timeline with sine wave background.
"""
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QMouseEvent, QAction
from PySide6.QtCore import Qt, QPoint, Signal
import math


class TimelineCanvas(QWidget):
    """Canvas widget for displaying timeline with sine wave background."""
    
    # Signal to request new chapter at position
    new_chapter_requested = Signal(float, float)  # canvas x, y position
    
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
