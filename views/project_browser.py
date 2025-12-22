"""
Project browser dialog for BlueWriter.
Allows creating and opening projects.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from models.project import Project
from database.connection import DatabaseManager, get_default_db_path


class ProjectBrowserDialog(QDialog):
    """Dialog for creating and opening projects."""
    
    project_selected = Signal(int)  # Emits project ID when selected
    
    def __init__(self, parent=None) -> None:
        """Initialize the project browser dialog."""
        super().__init__(parent)
        self.setWindowTitle("Project Browser")
        self.setModal(True)
        self.resize(500, 400)
        
        self.selected_project_id = None
        self.setup_ui()
        self.refresh_project_list()
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # New project tab
        new_project_tab = self.create_new_project_tab()
        self.tab_widget.addTab(new_project_tab, "New Project")
        
        # Open project tab
        open_project_tab = self.create_open_project_tab()
        self.tab_widget.addTab(open_project_tab, "Open Project")
        
        layout.addWidget(self.tab_widget)
        
        # Button box
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

    def create_new_project_tab(self) -> QWidget:
        """Create the new project tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Name field
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setFixedWidth(80)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter project name...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Description field
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optional description...")
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)
        
        layout.addStretch()
        
        # Create button
        create_button = QPushButton("Create Project")
        create_button.clicked.connect(self.create_new_project)
        layout.addWidget(create_button)
        
        return widget
    
    def create_open_project_tab(self) -> QWidget:
        """Create the open project tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Label
        layout.addWidget(QLabel("Select a project to open:"))
        
        # Projects list (using QListWidget for simplicity)
        self.projects_list = QListWidget()
        self.projects_list.itemDoubleClicked.connect(self.on_project_double_clicked)
        self.projects_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.projects_list)
        
        # Open button
        self.open_button = QPushButton("Open Selected Project")
        self.open_button.clicked.connect(self.open_selected_project)
        self.open_button.setEnabled(False)
        layout.addWidget(self.open_button)
        
        return widget
    
    def create_new_project(self) -> None:
        """Handle new project creation."""
        name = self.name_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Project name cannot be empty.")
            return
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                project = Project.create(db, name, description)
            
            QMessageBox.information(self, "Success", f"Project '{name}' created successfully!")
            
            # Emit signal and close dialog
            self.project_selected.emit(project.id)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create project: {str(e)}")

    def on_project_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on project - open it."""
        project_id = item.data(Qt.UserRole)
        if project_id:
            self.project_selected.emit(project_id)
            self.accept()
    
    def on_selection_changed(self) -> None:
        """Enable/disable open button based on selection."""
        has_selection = len(self.projects_list.selectedItems()) > 0
        self.open_button.setEnabled(has_selection)
    
    def open_selected_project(self) -> None:
        """Handle opening selected project."""
        selected_items = self.projects_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a project to open.")
            return
        
        project_id = selected_items[0].data(Qt.UserRole)
        if project_id:
            self.project_selected.emit(project_id)
            self.accept()
    
    def refresh_project_list(self) -> None:
        """Reload projects from database."""
        self.projects_list.clear()
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                projects = Project.get_all(db)
            
            for project in projects:
                item = QListWidgetItem(project.name)
                item.setData(Qt.UserRole, project.id)
                # Add tooltip with description
                if project.description:
                    item.setToolTip(project.description)
                self.projects_list.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load projects: {str(e)}")
