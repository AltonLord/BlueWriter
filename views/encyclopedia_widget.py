"""
Encyclopedia widget for BlueWriter sidebar.
Displays and manages world-building entries.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QComboBox,
    QMessageBox, QMainWindow
)
from PySide6.QtCore import Qt, Signal

from models.encyclopedia_entry import EncyclopediaEntry, DEFAULT_CATEGORIES
from views.encyclopedia_editor_dock import EncyclopediaEditorDock
from database.connection import DatabaseManager, get_default_db_path


class EncyclopediaWidget(QWidget):
    """Widget for managing encyclopedia entries in the sidebar."""
    
    entry_selected = Signal(int)  # entry_id
    
    def __init__(self, project_id: int, parent=None) -> None:
        super().__init__(parent)
        self.project_id = project_id
        self.open_editors = {}  # Track open editors: {entry_id: EncyclopediaEditorDock}
        
        self.setup_ui()
        self.load_entries()
    
    def get_main_window(self) -> QMainWindow:
        """Find the main window in parent hierarchy."""
        widget = self.parent()
        while widget is not None:
            if isinstance(widget, QMainWindow):
                return widget
            widget = widget.parent()
        return None
    
    def setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QLabel("📚 Encyclopedia")
        header.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header)
        
        # Search/filter bar
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.textChanged.connect(self.filter_entries)
        filter_layout.addWidget(self.search_edit)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems(DEFAULT_CATEGORIES)
        self.category_filter.currentTextChanged.connect(self.filter_entries)
        self.category_filter.setMaximumWidth(100)
        filter_layout.addWidget(self.category_filter)
        
        layout.addLayout(filter_layout)
        
        # Entry tree (grouped by category)
        self.entry_tree = QTreeWidget()
        self.entry_tree.setHeaderHidden(True)
        self.entry_tree.setIndentation(15)
        self.entry_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.entry_tree)
        
        # Add button
        add_btn = QPushButton("+ New Entry")
        add_btn.clicked.connect(self.create_new_entry)
        layout.addWidget(add_btn)

    def load_entries(self) -> None:
        """Load all entries from database and populate tree."""
        self.entry_tree.clear()
        self.category_items = {}
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                entries = EncyclopediaEntry.get_by_project(db, self.project_id)
            
            for entry in entries:
                self.add_entry_to_tree(entry)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load entries: {str(e)}")
    
    def add_entry_to_tree(self, entry: EncyclopediaEntry) -> None:
        """Add an entry to the tree under its category."""
        if entry.category not in self.category_items:
            cat_item = QTreeWidgetItem(self.entry_tree)
            cat_item.setText(0, f"📁 {entry.category}")
            cat_item.setExpanded(True)
            cat_item.setData(0, Qt.UserRole, None)
            self.category_items[entry.category] = cat_item
        
        cat_item = self.category_items[entry.category]
        
        entry_item = QTreeWidgetItem(cat_item)
        entry_item.setText(0, entry.name)
        entry_item.setData(0, Qt.UserRole, entry.id)
        # Clean tooltip - strip HTML
        plain_content = entry.content[:200] if entry.content else ""
        entry_item.setToolTip(0, plain_content + "..." if len(plain_content) >= 200 else plain_content)
    
    def filter_entries(self) -> None:
        """Filter displayed entries based on search and category."""
        search_text = self.search_edit.text().strip().lower()
        selected_category = self.category_filter.currentText()
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                if search_text:
                    entries = EncyclopediaEntry.search(db, self.project_id, search_text)
                else:
                    entries = EncyclopediaEntry.get_by_project(db, self.project_id)
            
            if selected_category != "All Categories":
                entries = [e for e in entries if e.category == selected_category]
            
            self.entry_tree.clear()
            self.category_items = {}
            
            for entry in entries:
                self.add_entry_to_tree(entry)
                
        except Exception as e:
            pass  # Silently handle filter errors
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on tree item."""
        entry_id = item.data(0, Qt.UserRole)
        if entry_id is not None:
            self.open_entry_editor(entry_id)

    def open_entry_editor(self, entry_id: int) -> None:
        """Open dockable editor for existing entry."""
        # Check if already open
        if entry_id in self.open_editors:
            editor = self.open_editors[entry_id]
            editor.show()
            editor.raise_()
            editor.setFocus()
            return
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                entry = EncyclopediaEntry.get_by_id(db, entry_id)
            
            if entry:
                self._create_editor(entry)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load entry: {str(e)}")
    
    def create_new_entry(self) -> None:
        """Create a new encyclopedia entry."""
        new_entry = EncyclopediaEntry(project_id=self.project_id)
        self._create_editor(new_entry)
    
    def _create_editor(self, entry: EncyclopediaEntry) -> None:
        """Create and show a dockable editor."""
        main_window = self.get_main_window()
        if not main_window:
            QMessageBox.critical(self, "Error", "Could not find main window")
            return
        
        editor = EncyclopediaEditorDock(entry, main_window)
        editor.entry_saved.connect(self.on_entry_saved)
        editor.entry_deleted.connect(self.on_entry_deleted)
        editor.entry_closed.connect(self.on_editor_closed)
        
        # Add to main window as dock widget
        main_window.addDockWidget(Qt.RightDockWidgetArea, editor)
        
        # Float it for cleaner experience
        editor.setFloating(True)
        editor.resize(600, 450)
        
        # Track if it has an ID
        if entry.id:
            self.open_editors[entry.id] = editor
    
    def on_entry_saved(self, entry: EncyclopediaEntry) -> None:
        """Handle entry save - refresh tree and track editor."""
        # If this was a new entry, now track it
        if entry.id and entry.id not in self.open_editors:
            # Find the editor that saved this
            for editor in self.findChildren(EncyclopediaEditorDock):
                if editor.entry.id == entry.id:
                    self.open_editors[entry.id] = editor
                    break
        self.load_entries()
    
    def on_entry_deleted(self, entry_id: int) -> None:
        """Handle entry deletion - refresh tree."""
        if entry_id in self.open_editors:
            del self.open_editors[entry_id]
        self.load_entries()
    
    def on_editor_closed(self, entry_id: int) -> None:
        """Handle editor close - remove from tracking."""
        if entry_id in self.open_editors:
            del self.open_editors[entry_id]
