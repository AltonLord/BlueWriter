"""
Chapter editor dialog for BlueWriter.
Allows editing of chapter content and metadata.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QLineEdit, QPushButton, QFormLayout,
    QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from models.chapter import Chapter
from database.connection import DatabaseManager, get_default_db_path


class ChapterEditor(QDialog):
    """Dialog for editing chapter details."""
    
    chapter_saved = Signal(Chapter)
    
    def __init__(self, chapter: Chapter, parent=None) -> None:
        """Initialize the chapter editor dialog."""
        super().__init__(parent)
        self.chapter = chapter
        self.db_manager = DatabaseManager(get_default_db_path())
        
        self.setWindowTitle(f"Edit Chapter: {chapter.title}")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        self.load_chapter_data()
    
    def setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Form for metadata
        form = QFormLayout()
        
        # Title
        self.title_input = QLineEdit()
        form.addRow("Title:", self.title_input)
        
        # Summary (2-3 lines shown on sticky note)
        self.summary_input = QTextEdit()
        self.summary_input.setMaximumHeight(80)
        self.summary_input.setPlaceholderText("Brief 2-3 sentence summary shown on the sticky note...")
        form.addRow("Summary:", self.summary_input)
        
        # Color picker
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setAutoFillBackground(True)
        color_layout.addWidget(self.color_preview)
        
        color_btn = QPushButton("Choose Color")
        color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(color_btn)
        color_layout.addStretch()
        form.addRow("Note Color:", color_layout)
        
        layout.addLayout(form)

        # Content editor (main chapter text)
        layout.addWidget(QLabel("Content:"))
        self.content_editor = QTextEdit()
        self.content_editor.setPlaceholderText("Write your chapter content here...")
        layout.addWidget(self.content_editor, 1)  # Stretch factor 1
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_chapter)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def load_chapter_data(self) -> None:
        """Populate fields from chapter."""
        self.title_input.setText(self.chapter.title or "")
        self.summary_input.setPlainText(self.chapter.summary or "")
        self.content_editor.setHtml(self.chapter.content or "")
        self.update_color_preview()
    
    def update_color_preview(self) -> None:
        """Update the color preview label."""
        color = self.chapter.color or "#FFFF88"
        palette = self.color_preview.palette()
        palette.setColor(self.color_preview.backgroundRole(), QColor(color))
        self.color_preview.setPalette(palette)
        self.color_preview.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
    
    def pick_color(self) -> None:
        """Open color picker dialog."""
        current = QColor(self.chapter.color or "#FFFF88")
        color = QColorDialog.getColor(current, self, "Choose Sticky Note Color")
        if color.isValid():
            self.chapter.color = color.name()
            self.update_color_preview()
    
    def save_chapter(self) -> None:
        """Save chapter to database and emit signal."""
        # Update chapter object
        self.chapter.title = self.title_input.text().strip() or "Untitled"
        self.chapter.summary = self.summary_input.toPlainText().strip()
        self.chapter.content = self.content_editor.toHtml()
        
        # Save to database
        with self.db_manager as conn:
            self.chapter.update(conn)
        
        # Emit signal
        self.chapter_saved.emit(self.chapter)
        self.accept()
