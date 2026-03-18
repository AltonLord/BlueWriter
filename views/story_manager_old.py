"""
Story management UI for BlueWriter.
Allows managing stories within a project.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer

from models.story import Story
from database.connection import DatabaseManager, get_default_db_path


class StoryManagerWidget(QWidget):
    """Widget for managing stories within a project."""
    
    story_selected = Signal(int)  # Emits story ID when selected
    story_added = Signal(int)     # Emits story ID when added
    
    def __init__(self, project_id: int, parent=None) -> None:
        super().__init__(parent)
        self.project_id = project_id
        self.current_story_id = None
        self.synopsis_edits = {}  # Track QTextEdit widgets by story_id
        
        self.setup_ui()
        self.load_stories()
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # New Story button
        new_story_button = QPushButton("+ New Story")
        new_story_button.clicked.connect(self.create_new_story)
        layout.addWidget(new_story_button)
        
        # Tab widget for stories
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)  # Don't allow closing for now
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_widget)
        
        # Placeholder when no stories
        self.placeholder = QLabel("No stories yet.\nClick '+ New Story' to create one.")
        self.placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.placeholder)

    def load_stories(self) -> None:
        """Load all stories for the current project."""
        try:
            with DatabaseManager(get_default_db_path()) as db:
                stories = Story.get_by_project(db, self.project_id)
            
            # Clear existing tabs
            self.tab_widget.blockSignals(True)  # Prevent signals while rebuilding
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
            self.synopsis_edits.clear()
            self.tab_widget.blockSignals(False)
            
            # Add tabs for each story
            for story in stories:
                self.add_story_tab(story)
            
            # Update placeholder visibility
            if self.tab_widget.count() > 0:
                self.placeholder.hide()
                # Auto-select first story after a brief delay to ensure UI is ready
                QTimer.singleShot(100, self.select_first_story)
            else:
                self.placeholder.show()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load stories: {str(e)}")
    
    def select_first_story(self) -> None:
        """Select the first story tab and emit signal."""
        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(0)
            # Manually trigger since we blocked signals during load
            self.on_tab_changed(0)
    
    def add_story_tab(self, story: Story) -> None:
        """Add a tab for a story."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status indicator for locked stories
        if story.is_locked:
            status_label = QLabel("🔒 <b>Final Published</b> - Story is locked from editing")
            status_label.setStyleSheet("color: green; padding: 5px; background: #1a3a1a; border-radius: 3px;")
            layout.addWidget(status_label)
        elif story.is_published:
            status_label = QLabel("📝 Rough Draft Published - Still editable")
            status_label.setStyleSheet("color: #6699ff; padding: 5px; background: #1a2a3a; border-radius: 3px;")
            layout.addWidget(status_label)
        
        # Title (editable, but disabled if locked)
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        title_edit = QLineEdit(story.title)
        title_edit.setProperty("story_id", story.id)
        title_edit.setEnabled(not story.is_locked)
        title_edit.editingFinished.connect(lambda: self.save_story_title(story.id, title_edit))
        title_layout.addWidget(title_edit)
        layout.addLayout(title_layout)
        
        # Synopsis (editable with auto-save, but disabled if locked)
        layout.addWidget(QLabel("Synopsis:"))
        synopsis_edit = QTextEdit()
        synopsis_edit.setPlainText(story.synopsis or "")
        synopsis_edit.setMaximumHeight(120)
        synopsis_edit.setPlaceholderText("Enter story synopsis...")
        synopsis_edit.setEnabled(not story.is_locked)
        synopsis_edit.textChanged.connect(lambda: self.on_synopsis_changed(story.id))
        layout.addWidget(synopsis_edit)
        
        # Store reference for saving
        self.synopsis_edits[story.id] = synopsis_edit
        
        # Save button for synopsis (hidden if locked)
        save_btn = QPushButton("Save Synopsis")
        save_btn.clicked.connect(lambda: self.save_synopsis(story.id))
        save_btn.setEnabled(not story.is_locked)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        # Add tab with lock icon in title if locked
        tab_title = f"🔒 {story.title}" if story.is_locked else story.title
        tab_index = self.tab_widget.addTab(tab, tab_title)
        tab.setProperty("story_id", story.id)

    def on_tab_changed(self, index: int) -> None:
        """Handle tab selection - emit story_selected signal."""
        if index >= 0:
            tab = self.tab_widget.widget(index)
            if tab:
                story_id = tab.property("story_id")
                if story_id is not None:
                    self.current_story_id = story_id
                    self.story_selected.emit(story_id)
                    self.placeholder.hide()
    
    def on_synopsis_changed(self, story_id: int) -> None:
        """Mark synopsis as modified (visual feedback could be added here)."""
        # Could add a "modified" indicator to the tab
        pass
    
    def save_synopsis(self, story_id: int) -> None:
        """Save the synopsis for a story."""
        if story_id not in self.synopsis_edits:
            return
        
        synopsis_text = self.synopsis_edits[story_id].toPlainText()
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                story = Story.get_by_id(db, story_id)
                if story:
                    story.synopsis = synopsis_text
                    story.update(db)
            
            QMessageBox.information(self, "Saved", "Synopsis saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save synopsis: {str(e)}")
    
    def save_story_title(self, story_id: int, title_edit: QLineEdit) -> None:
        """Save the title for a story."""
        new_title = title_edit.text().strip()
        if not new_title:
            return
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                story = Story.get_by_id(db, story_id)
                if story:
                    story.title = new_title
                    story.update(db)
            
            # Update tab title
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if tab.property("story_id") == story_id:
                    self.tab_widget.setTabText(i, new_title)
                    break
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save title: {str(e)}")
    
    def create_new_story(self) -> None:
        """Create a new story."""
        try:
            with DatabaseManager(get_default_db_path()) as db:
                story = Story.create(db, self.project_id, "New Story", "")
            
            self.add_story_tab(story)
            self.placeholder.hide()
            
            # Select the new tab
            new_index = self.tab_widget.count() - 1
            self.tab_widget.setCurrentIndex(new_index)
            
            # Emit signals
            self.story_added.emit(story.id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create story: {str(e)}")
