"""
Encyclopedia entry editor dialog for BlueWriter.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal

from models.encyclopedia_entry import EncyclopediaEntry, DEFAULT_CATEGORIES
from database.connection import DatabaseManager, get_default_db_path


class EncyclopediaEditor(QDialog):
    """Dialog for editing encyclopedia entries."""
    
    entry_saved = Signal(EncyclopediaEntry)
    entry_deleted = Signal(int)  # entry_id
    
    def __init__(self, entry: EncyclopediaEntry, parent=None) -> None:
        super().__init__(parent)
        self.entry = entry
        self.is_new = entry.id is None
        
        self.setWindowTitle("New Entry" if self.is_new else f"Edit: {entry.name}")
        self.setModal(True)
        self.resize(500, 450)
        
        self.setup_ui()
        self.load_entry_data()
    
    def setup_ui(self) -> None:
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        
        # Category selector
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(DEFAULT_CATEGORIES)
        self.category_combo.setEditable(True)  # Allow custom categories
        cat_layout.addWidget(self.category_combo)
        layout.addLayout(cat_layout)
        
        # Name field
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Entry name...")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Tags field
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags...")
        tags_layout.addWidget(self.tags_edit)
        layout.addLayout(tags_layout)
        
        # Content editor
        layout.addWidget(QLabel("Content:"))
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Enter details about this entry...")
        layout.addWidget(self.content_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        
        if not self.is_new:
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("color: #cc4444;")
            delete_btn.clicked.connect(self.delete_entry)
            btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_entry)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def load_entry_data(self) -> None:
        """Load entry data into form fields."""
        if self.entry.category:
            idx = self.category_combo.findText(self.entry.category)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            else:
                self.category_combo.setEditText(self.entry.category)
        
        self.name_edit.setText(self.entry.name or "")
        self.tags_edit.setText(self.entry.tags or "")
        self.content_edit.setPlainText(self.entry.content or "")
    
    def save_entry(self) -> None:
        """Save the entry to database."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid", "Name cannot be empty.")
            return
        
        self.entry.name = name
        self.entry.category = self.category_combo.currentText().strip() or "General"
        self.entry.tags = self.tags_edit.text().strip()
        self.entry.content = self.content_edit.toPlainText()
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                if self.is_new:
                    # Create new entry
                    new_entry = EncyclopediaEntry.create(
                        db,
                        project_id=self.entry.project_id,
                        name=self.entry.name,
                        category=self.entry.category,
                        content=self.entry.content,
                        tags=self.entry.tags
                    )
                    self.entry = new_entry
                else:
                    self.entry.update(db)
            
            self.entry_saved.emit(self.entry)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
    
    def delete_entry(self) -> None:
        """Delete the entry after confirmation."""
        result = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{self.entry.name}'?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            try:
                with DatabaseManager(get_default_db_path()) as db:
                    self.entry.delete(db)
                self.entry_deleted.emit(self.entry.id)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")
