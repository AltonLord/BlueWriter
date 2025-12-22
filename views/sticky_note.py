"""
Sticky note widget for BlueWriter timeline.
Displays chapter information as draggable notes.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRectF, QPoint, Signal

from models.chapter import Chapter


class StickyNote(QWidget):
    """Draggable sticky note representing a chapter on the timeline."""
    
    # Signals
    double_clicked = Signal(int)  # Emits chapter ID
    position_changed = Signal(int, float, float)  # chapter_id, canvas_x, canvas_y
    
    def __init__(self, chapter: Chapter, parent=None) -> None:
        """Initialize the sticky note from a chapter."""
        super().__init__(parent)
        
        self.chapter = chapter
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        
        # Canvas coordinates (world position)
        self.canvas_x = chapter.board_x
        self.canvas_y = chapter.board_y
        
        # Set size
        self.setFixedSize(160, 100)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.setCursor(Qt.OpenHandCursor)
    
    def update_from_chapter(self, chapter: Chapter) -> None:
        """Update display from chapter data."""
        self.chapter = chapter
        self.canvas_x = chapter.board_x
        self.canvas_y = chapter.board_y
        self.update()
    
    def set_canvas_position(self, x: float, y: float) -> None:
        """Set position in canvas coordinates."""
        self.canvas_x = x
        self.canvas_y = y
    
    def get_canvas_position(self) -> tuple:
        """Get position in canvas coordinates."""
        return (self.canvas_x, self.canvas_y)

    def paintEvent(self, event) -> None:
        """Paint the sticky note."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get note color (default yellow if not set)
        color = QColor(self.chapter.color if self.chapter.color else "#FFFF88")
        
        # Draw shadow
        shadow_rect = QRectF(4, 4, self.width() - 4, self.height() - 4)
        painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, 5, 5)

        # Draw main note background
        note_rect = QRectF(0, 0, self.width() - 4, self.height() - 4)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawRoundedRect(note_rect, 5, 5)
        
        # Draw title
        painter.setPen(QPen(QColor(0, 0, 0)))
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)
        
        title_rect = QRectF(8, 8, self.width() - 20, 22)
        title = self.chapter.title if self.chapter.title else "Untitled"
        painter.drawText(title_rect, Qt.AlignLeft | Qt.TextSingleLine, title)
        
        # Draw separator line
        painter.setPen(QPen(color.darker(115), 1))
        painter.drawLine(8, 32, self.width() - 12, 32)
        
        # Draw summary
        painter.setPen(QPen(QColor(60, 60, 60)))
        summary_font = QFont()
        summary_font.setPointSize(8)
        painter.setFont(summary_font)
        
        summary_rect = QRectF(8, 36, self.width() - 20, self.height() - 44)
        summary = self.chapter.summary if self.chapter.summary else "No summary"
        if len(summary) > 80:
            summary = summary[:77] + "..."
        painter.drawText(summary_rect, Qt.AlignLeft | Qt.TextWordWrap, summary)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.raise_()
            event.accept()
    
    def mouseMoveEvent(self, event) -> None:
        """Handle drag movement."""
        if self.is_dragging:
            # Calculate new screen position
            new_screen_pos = self.mapToParent(event.pos() - self.drag_start_pos)
            self.move(new_screen_pos)
            
            # Update canvas coordinates via parent
            parent = self.parent()
            if parent and hasattr(parent, 'screen_to_canvas'):
                cx, cy = parent.screen_to_canvas(new_screen_pos.x(), new_screen_pos.y())
                self.canvas_x = cx
                self.canvas_y = cy
            event.accept()
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release - emit position change with canvas coordinates."""
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setCursor(Qt.OpenHandCursor)
            # Emit canvas coordinates
            self.position_changed.emit(self.chapter.id, self.canvas_x, self.canvas_y)
            event.accept()
    
    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click to open editor."""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.chapter.id)
            event.accept()
