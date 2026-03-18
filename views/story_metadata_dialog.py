"""
Story metadata dialog for BlueWriter.
Allows editing story title, synopsis, representation type, and outline color.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QDialogButtonBox, QColorDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services.story_service import StoryDTO


class StoryMetadataDialog(QDialog):
    """Dialog for editing story title, synopsis, representation type, color."""

    def __init__(self, story_dto: StoryDTO, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Story: {story_dto.title}")
        self.setMinimumWidth(400)
        self._story = story_dto
        self._selected_color = story_dto.outline_color or "#4A90D9"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        layout.addWidget(QLabel("Title:"))
        self._title_edit = QLineEdit(self._story.title)
        layout.addWidget(self._title_edit)

        # Synopsis
        layout.addWidget(QLabel("Synopsis:"))
        self._synopsis_edit = QTextEdit()
        self._synopsis_edit.setPlainText(self._story.synopsis or "")
        self._synopsis_edit.setMaximumHeight(120)
        self._synopsis_edit.setPlaceholderText("Enter story synopsis...")
        layout.addWidget(self._synopsis_edit)

        # Representation type
        layout.addWidget(QLabel("Canvas Representation:"))
        self._rep_combo = QComboBox()
        self._rep_combo.addItem("Box (bounding rectangle)", "box")
        self._rep_combo.addItem("String (red yarn path)", "string")
        current_rep = self._story.representation_type or "box"
        idx = 0 if current_rep == "box" else 1
        self._rep_combo.setCurrentIndex(idx)
        layout.addWidget(self._rep_combo)

        # Outline color
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Outline Color:"))
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(60, 28)
        self._update_color_button()
        self._color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        layout.addLayout(color_row)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_color_button(self):
        self._color_btn.setStyleSheet(
            f"background-color: {self._selected_color}; border: 1px solid #666; border-radius: 3px;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._selected_color), self, "Choose Outline Color")
        if color.isValid():
            self._selected_color = color.name()
            self._update_color_button()

    def get_title(self) -> str:
        return self._title_edit.text().strip()

    def get_synopsis(self) -> str:
        return self._synopsis_edit.toPlainText()

    def get_representation_type(self) -> str:
        return self._rep_combo.currentData()

    def get_outline_color(self) -> str:
        return self._selected_color
