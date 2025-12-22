"""
Export dialog for BlueWriter.
Handles exporting projects to portable formats.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt

from models.project import Project
from models.story import Story
from models.encyclopedia_entry import EncyclopediaEntry
from utils.export import ProjectExporter
from database.connection import DatabaseManager, get_default_db_path


class ExportDialog(QDialog):
    """Dialog for exporting projects."""
    
    def __init__(self, project: Project, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.db_path = str(get_default_db_path())
        
        self.setWindowTitle(f"Export: {project.name}")
        self.setMinimumWidth(450)
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Project info
        info_group = QGroupBox("Project Information")
        info_layout = QVBoxLayout(info_group)
        
        self.title_label = QLabel(f"<b>{self.project.name}</b>")
        info_layout.addWidget(self.title_label)
        
        if self.project.description:
            desc_label = QLabel(self.project.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray;")
            info_layout.addWidget(desc_label)
        
        # Get counts
        with DatabaseManager(self.db_path) as conn:
            stories = Story.get_by_project(conn, self.project.id)
            entries = EncyclopediaEntry.get_by_project(conn, self.project.id)
        
        counts_text = f"Stories: {len(stories)} | Encyclopedia Entries: {len(entries)}"
        counts_label = QLabel(counts_text)
        info_layout.addWidget(counts_label)
        
        layout.addWidget(info_group)
        
        # Export format info
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        format_desc = QLabel(
            "<b>Zip Archive containing:</b><br>"
            "• <b>project.json</b> - Project metadata<br>"
            "• <b>stories/</b> - Each story in its own folder<br>"
            "  &nbsp;&nbsp;- story.json - Story metadata<br>"
            "  &nbsp;&nbsp;- chapter_XX_title.md - Chapters as Markdown<br>"
            "• <b>encyclopedia/</b> - Encyclopedia entries<br>"
            "  &nbsp;&nbsp;- entries.json - Entry metadata<br>"
            "  &nbsp;&nbsp;- Category/entry_name.md - Entries by category"
        )
        format_desc.setWordWrap(True)
        format_layout.addWidget(format_desc)
        
        layout.addWidget(format_group)
        
        # Info about format
        info_label = QLabel(
            "<i>This export format is portable and can be:\n"
            "• Imported into other writing tools\n"
            "• Edited with any text editor\n"
            "• Stored as a backup\n"
            "• Version controlled with Git</i>"
        )
        info_label.setStyleSheet("color: gray;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self.do_export)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)
    
    def do_export(self) -> None:
        """Execute the export process."""
        # Get save location
        default_name = f"{self.project.name}_export.zip"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Project",
            str(Path.home() / default_name),
            "Zip Archives (*.zip)"
        )
        
        if not file_path:
            return
        
        # Show progress
        progress = QProgressDialog("Exporting...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            exporter = ProjectExporter(self.db_path)
            output_path = exporter.export_project(self.project.id, file_path)
            
            progress.close()
            
            QMessageBox.information(
                self,
                "Exported",
                f"Successfully exported to:\n{output_path}"
            )
            
            self.accept()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")
