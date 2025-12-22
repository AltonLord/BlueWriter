"""
Import dialog for BlueWriter.
Handles importing projects from exported ZIP archives.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt

from utils.importer import ProjectImporter
from database.connection import get_default_db_path


class ImportDialog(QDialog):
    """Dialog for importing projects from ZIP archives."""
    
    # Signal to notify when import is complete
    project_imported = None  # Will be set up as Signal in __init__
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.db_path = str(get_default_db_path())
        self.selected_file = None
        self.imported_project_id = None
        
        self.setWindowTitle("Import Project")
        self.setMinimumWidth(500)
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        info_group = QGroupBox("Import from BlueWriter Export")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(
            "<p>Import a project from a BlueWriter export ZIP archive.</p>"
            "<p>The archive should contain:</p>"
            "<ul>"
            "<li><b>project.json</b> - Project metadata</li>"
            "<li><b>stories/</b> - Story folders with chapters as Markdown</li>"
            "<li><b>encyclopedia/</b> - Encyclopedia entries (optional)</li>"
            "</ul>"
            "<p>A new project will be created with all stories, chapters, "
            "and encyclopedia entries from the archive.</p>"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # File selection
        file_group = QGroupBox("Select Archive")
        file_layout = QHBoxLayout(file_group)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: gray;")
        file_layout.addWidget(self.file_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(file_group)
        
        # Notes
        notes_label = QLabel(
            "<i>Note: If a project with the same name already exists, "
            "a number will be added to make it unique.</i>"
        )
        notes_label.setStyleSheet("color: gray;")
        notes_label.setWordWrap(True)
        layout.addWidget(notes_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.do_import)
        self.import_btn.setEnabled(False)
        btn_layout.addWidget(self.import_btn)
        
        layout.addLayout(btn_layout)
    
    def browse_file(self) -> None:
        """Open file browser to select ZIP archive."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Export Archive",
            str(Path.home()),
            "ZIP Archives (*.zip)"
        )
        
        if file_path:
            self.selected_file = file_path
            # Show just the filename
            filename = Path(file_path).name
            self.file_label.setText(filename)
            self.file_label.setStyleSheet("color: black;")
            self.import_btn.setEnabled(True)
    
    def do_import(self) -> None:
        """Execute the import process."""
        if not self.selected_file:
            return
        
        # Show progress
        progress = QProgressDialog("Importing project...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            importer = ProjectImporter(self.db_path)
            project_id, stats = importer.import_from_zip(self.selected_file)
            
            self.imported_project_id = project_id
            
            progress.close()
            
            # Show success message
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported project!\n\n"
                f"Stories: {stats['stories']}\n"
                f"Chapters: {stats['chapters']}\n"
                f"Encyclopedia entries: {stats['encyclopedia_entries']}"
            )
            
            self.accept()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Import Failed", f"Error importing project:\n{str(e)}")
    
    def get_imported_project_id(self) -> int:
        """Return the ID of the imported project."""
        return self.imported_project_id
