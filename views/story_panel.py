"""
Story panel UI for BlueWriter.
Vertical card list replacing the old tab-based StoryManagerWidget.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QMenu, QSizePolicy,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QMouseEvent

from services.story_service import StoryDTO


class StoryCard(QFrame):
    """A card widget representing a single story in the sidebar."""

    outline_edit_requested = Signal(int)   # story_id
    frame_story_requested = Signal(int)    # story_id
    delete_requested = Signal(int)         # story_id
    edit_metadata_requested = Signal(int)  # story_id

    def __init__(self, story_dto: StoryDTO, parent=None):
        super().__init__(parent)
        self.story_id = story_dto.id
        self._story = story_dto
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(90)
        self.setMaximumHeight(120)

        # Style with story's outline color
        color = story_dto.outline_color or "#4A90D9"
        self.setStyleSheet(f"""
            StoryCard {{
                border: 2px solid {color};
                border-radius: 6px;
                background-color: #2a2a2a;
                padding: 6px;
            }}
            StoryCard:hover {{
                background-color: #333333;
            }}
        """)

        self._setup_ui(story_dto)

    def _setup_ui(self, story: StoryDTO):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Top row: colored dot + title + menu button
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        # Colored dot indicator
        dot_label = QLabel("\u25cf")  # bullet
        color = story.outline_color or "#4A90D9"
        rep_type = story.representation_type or "box"
        tooltip = f"Type: {rep_type}"
        dot_label.setToolTip(tooltip)
        dot_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        dot_label.setFixedWidth(16)
        top_row.addWidget(dot_label)

        # Title
        title_label = QLabel(story.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #e0e0e0;")
        title_label.setWordWrap(False)
        top_row.addWidget(title_label, 1)

        # Lock icon if published
        if story.is_locked:
            lock_label = QLabel("\U0001f512")
            lock_label.setToolTip("Final Published - Locked")
            top_row.addWidget(lock_label)

        # Menu button
        menu_btn = QPushButton("\u22ee")  # vertical ellipsis
        menu_btn.setFixedSize(24, 24)
        menu_btn.setStyleSheet("""
            QPushButton { border: none; color: #aaa; font-size: 16px; }
            QPushButton:hover { color: #fff; background: #444; border-radius: 3px; }
        """)
        menu_btn.clicked.connect(self._show_menu)
        top_row.addWidget(menu_btn)

        layout.addLayout(top_row)

        # Synopsis (2 lines, elided)
        synopsis = story.synopsis or ""
        if len(synopsis) > 100:
            synopsis = synopsis[:97] + "..."
        synopsis_label = QLabel(synopsis)
        synopsis_label.setStyleSheet("color: #999; font-size: 10px;")
        synopsis_label.setWordWrap(True)
        synopsis_label.setMaximumHeight(30)
        layout.addWidget(synopsis_label)

        # Edit Outline button
        edit_btn = QPushButton("Edit Outline")
        edit_btn.setFixedHeight(22)
        edit_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a; color: #ccc; border: 1px solid #555;
                border-radius: 3px; font-size: 10px; padding: 2px 8px;
            }
            QPushButton:hover { background: #4a4a4a; color: #fff; }
        """)
        edit_btn.clicked.connect(lambda: self.outline_edit_requested.emit(self.story_id))
        layout.addWidget(edit_btn, alignment=Qt.AlignLeft)

    def _show_menu(self):
        menu = QMenu(self)
        menu.addAction("Edit Metadata", lambda: self.edit_metadata_requested.emit(self.story_id))
        menu.addSeparator()
        delete_action = menu.addAction("Delete Story")
        delete_action.setToolTip("Removes story grouping. Chapters are kept.")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.story_id))
        menu.exec(self.mapToGlobal(self.rect().topRight()))

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.frame_story_requested.emit(self.story_id)
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Edit Metadata", lambda: self.edit_metadata_requested.emit(self.story_id))
        menu.addSeparator()
        delete_action = menu.addAction("Delete Story")
        delete_action.setToolTip("Removes story grouping. Chapters are kept.")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.story_id))
        menu.exec(event.globalPos())

    def update_from_dto(self, story_dto: StoryDTO):
        """Rebuild card content from updated DTO."""
        self._story = story_dto
        self.story_id = story_dto.id
        # Clear and rebuild layout
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    while item.layout().count():
                        sub = item.layout().takeAt(0)
                        if sub.widget():
                            sub.widget().deleteLater()
        self._setup_ui(story_dto)


class StoryPanelWidget(QWidget):
    """Panel showing story cards in a vertical list."""

    story_created = Signal(int)            # story_id
    frame_story_requested = Signal(int)    # story_id
    outline_edit_requested = Signal(int)   # story_id
    delete_requested = Signal(int)         # story_id
    edit_metadata_requested = Signal(int)  # story_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[int, StoryCard] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        # "+ New Story" button at top
        new_story_btn = QPushButton("+ New Story")
        new_story_btn.setStyleSheet("""
            QPushButton {
                background: #3a5a3a; color: #ccc; border: 1px solid #5a7a5a;
                border-radius: 4px; padding: 6px; font-weight: bold;
            }
            QPushButton:hover { background: #4a6a4a; color: #fff; }
        """)
        new_story_btn.clicked.connect(self._on_new_story_clicked)
        layout.addWidget(new_story_btn)

        # Scrollable card list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(4)
        self._cards_layout.addStretch()  # Push cards to top

        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll)

        # Placeholder
        self._placeholder = QLabel("No stories yet.\nClick '+ New Story' to create one.")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #888;")
        layout.addWidget(self._placeholder)

    def _on_new_story_clicked(self):
        self.story_created.emit(0)  # 0 = signal to create new story

    def load_stories(self, stories: list):
        """Load a list of StoryDTO objects into the panel."""
        # Clear existing cards
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # Remove stretch
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            # Don't delete cards here, already handled above

        # Add cards (newest at top = reverse order)
        for story_dto in reversed(stories):
            self._add_card(story_dto)

        self._cards_layout.addStretch()
        self._placeholder.setVisible(len(stories) == 0)

    def _add_card(self, story_dto: StoryDTO):
        card = StoryCard(story_dto, parent=self._cards_container)
        card.frame_story_requested.connect(self.frame_story_requested.emit)
        card.outline_edit_requested.connect(self.outline_edit_requested.emit)
        card.delete_requested.connect(self.delete_requested.emit)
        card.edit_metadata_requested.connect(self.edit_metadata_requested.emit)
        self._cards[story_dto.id] = card
        # Insert before stretch
        idx = self._cards_layout.count() - 1 if self._cards_layout.count() > 0 else 0
        self._cards_layout.insertWidget(idx, card)

    def add_story(self, story_dto: StoryDTO):
        """Add a single story card (e.g. after creation)."""
        self._add_card(story_dto)
        self._placeholder.hide()

    def remove_story(self, story_id: int):
        """Remove a story card."""
        if story_id in self._cards:
            card = self._cards.pop(story_id)
            card.setParent(None)
            card.deleteLater()
        if not self._cards:
            self._placeholder.show()
