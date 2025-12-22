"""
Publishing dialog for BlueWriter.
Handles rough draft and final draft publishing to PDF, DOCX, and EPUB.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QRadioButton, QFileDialog, QMessageBox,
    QProgressDialog, QCheckBox, QComboBox, QLineEdit,
    QButtonGroup
)
from PySide6.QtCore import Qt

from models.story import Story, STATUS_DRAFT, STATUS_ROUGH_PUBLISHED, STATUS_FINAL_PUBLISHED
from utils.publishing import StoryPublisher, get_story_stats
from database.connection import get_default_db_path


class PublishDialog(QDialog):
    """Dialog for publishing stories to PDF, DOCX, or EPUB."""
    
    def __init__(self, story: Story, parent=None) -> None:
        super().__init__(parent)
        self.story = story
        self.db_path = str(get_default_db_path())
        
        self.setWindowTitle(f"Publish: {story.title}")
        self.setMinimumWidth(500)
        
        self.setup_ui()
        self.update_status_display()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Story info
        info_group = QGroupBox("Story Information")
        info_layout = QVBoxLayout(info_group)
        
        self.title_label = QLabel(f"<b>{self.story.title}</b>")
        info_layout.addWidget(self.title_label)
        
        # Get stats
        stats = get_story_stats(self.db_path, self.story.id)
        stats_text = (f"Chapters: {stats['chapter_count']} | "
                     f"Words: {stats['total_words']:,} | "
                     f"Avg per chapter: {stats['avg_chapter_words']:,}")
        self.stats_label = QLabel(stats_text)
        info_layout.addWidget(self.stats_label)
        
        self.status_label = QLabel()
        info_layout.addWidget(self.status_label)
        
        layout.addWidget(info_group)
        
        # Format selection
        format_group = QGroupBox("Output Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("PDF - Portable Document Format", "pdf")
        self.format_combo.addItem("DOCX - Word Document (for editors)", "docx")
        self.format_combo.addItem("EPUB - eBook (for Kindle, Apple Books)", "epub")
        self.format_combo.currentIndexChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        # Format descriptions
        self.format_desc = QLabel()
        self.format_desc.setWordWrap(True)
        self.format_desc.setStyleSheet("color: gray; padding: 5px;")
        format_layout.addWidget(self.format_desc)
        
        layout.addWidget(format_group)
        
        # Author name (for EPUB)
        self.author_group = QGroupBox("Author Information")
        author_layout = QHBoxLayout(self.author_group)
        author_layout.addWidget(QLabel("Author Name:"))
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Enter author name for ebook metadata")
        author_layout.addWidget(self.author_edit)
        self.author_group.hide()  # Only show for EPUB
        layout.addWidget(self.author_group)
        
        # Publishing type options
        type_group = QGroupBox("Publishing Type")
        type_layout = QVBoxLayout(type_group)
        
        self.type_button_group = QButtonGroup(self)
        
        self.rough_radio = QRadioButton("Rough Draft")
        self.rough_radio.setToolTip(
            "Creates output with DRAFT indicator.\n"
            "You can continue editing the story after publishing."
        )
        type_layout.addWidget(self.rough_radio)
        self.type_button_group.addButton(self.rough_radio)
        
        rough_desc = QLabel("  • Includes draft watermark/timestamp • Story remains editable")
        rough_desc.setStyleSheet("color: gray; margin-left: 20px;")
        type_layout.addWidget(rough_desc)
        
        type_layout.addSpacing(10)
        
        self.final_radio = QRadioButton("Final Draft")
        self.final_radio.setToolTip(
            "Creates clean output without watermark.\n"
            "WARNING: This will LOCK the story from further editing."
        )
        type_layout.addWidget(self.final_radio)
        self.type_button_group.addButton(self.final_radio)
        
        final_desc = QLabel("  • Clean format, no watermark • <b>⚠ LOCKS story from editing</b>")
        final_desc.setStyleSheet("color: #cc6600; margin-left: 20px;")
        type_layout.addWidget(final_desc)
        
        self.rough_radio.setChecked(True)
        
        layout.addWidget(type_group)
        
        # Options
        self.include_synopsis = QCheckBox("Include chapter summaries")
        self.include_synopsis.setChecked(True)
        layout.addWidget(self.include_synopsis)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.publish_btn = QPushButton("Publish...")
        self.publish_btn.clicked.connect(self.do_publish)
        btn_layout.addWidget(self.publish_btn)
        
        layout.addLayout(btn_layout)
        
        # Initialize format description
        self.on_format_changed(0)

    def on_format_changed(self, index: int) -> None:
        """Update UI based on selected format."""
        format_type = self.format_combo.currentData()
        
        descriptions = {
            'pdf': "PDF is ideal for sharing and printing. Preserves exact formatting across all devices.",
            'docx': "DOCX (Word) is the industry standard for editors. Allows track changes and comments for professional editing workflow.",
            'epub': "EPUB is the standard ebook format. Compatible with Amazon KDP, Apple Books, Kobo, and most e-readers."
        }
        
        self.format_desc.setText(descriptions.get(format_type, ""))
        
        # Show author field only for EPUB
        self.author_group.setVisible(format_type == 'epub')
    
    def update_status_display(self) -> None:
        """Update the status label based on story status."""
        status_map = {
            STATUS_DRAFT: ("Draft", "gray"),
            STATUS_ROUGH_PUBLISHED: ("Rough Published", "#6699ff"),
            STATUS_FINAL_PUBLISHED: ("Final Published (Locked)", "green")
        }
        
        status_text, color = status_map.get(self.story.status, ("Unknown", "gray"))
        self.status_label.setText(f"Current Status: <b style='color:{color}'>{status_text}</b>")
        
        # Disable final option if already final
        if self.story.status == STATUS_FINAL_PUBLISHED:
            self.final_radio.setEnabled(False)
            self.rough_radio.setEnabled(False)
            self.publish_btn.setEnabled(False)
            self.publish_btn.setText("Story is Locked")
    
    def do_publish(self) -> None:
        """Execute the publishing process."""
        is_final = self.final_radio.isChecked()
        format_type = self.format_combo.currentData()
        
        # Validate author for EPUB
        if format_type == 'epub' and not self.author_edit.text().strip():
            QMessageBox.warning(self, "Author Required", 
                              "Please enter an author name for the ebook.")
            self.author_edit.setFocus()
            return
        
        # Confirm final publish
        if is_final:
            result = QMessageBox.warning(
                self,
                "Confirm Final Publish",
                f"Publishing '{self.story.title}' as FINAL will:\n\n"
                "• Create a clean file without watermark\n"
                "• LOCK the story from further editing\n"
                "• Require unpublishing to make changes\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return
        
        # Get file extension and filter
        extensions = {
            'pdf': ("PDF Files (*.pdf)", ".pdf"),
            'docx': ("Word Documents (*.docx)", ".docx"),
            'epub': ("EPUB Files (*.epub)", ".epub")
        }
        file_filter, ext = extensions[format_type]
        
        # Get save location
        default_name = f"{self.story.title}_{'FINAL' if is_final else 'DRAFT'}{ext}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {format_type.upper()}",
            str(Path.home() / default_name),
            file_filter
        )
        
        if not file_path:
            return
        
        # Show progress
        progress = QProgressDialog("Publishing...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            publisher = StoryPublisher(self.db_path)
            include_synopsis = self.include_synopsis.isChecked()
            
            # Update story status
            if is_final:
                from database.connection import DatabaseManager
                with DatabaseManager(self.db_path) as conn:
                    story = Story.get_by_id(conn, self.story.id)
                    story.publish_final(conn)
            else:
                from database.connection import DatabaseManager
                with DatabaseManager(self.db_path) as conn:
                    story = Story.get_by_id(conn, self.story.id)
                    story.publish_rough(conn)
            
            # Generate output based on format
            if format_type == 'pdf':
                publisher.publish_to_pdf(
                    self.story.id,
                    file_path,
                    include_synopsis=include_synopsis,
                    draft_watermark=not is_final
                )
            elif format_type == 'docx':
                publisher.publish_to_docx(
                    self.story.id,
                    file_path,
                    include_synopsis=include_synopsis,
                    draft_watermark=not is_final
                )
            elif format_type == 'epub':
                publisher.publish_to_epub(
                    self.story.id,
                    file_path,
                    author=self.author_edit.text().strip(),
                    include_synopsis=include_synopsis
                )
            
            progress.close()
            
            QMessageBox.information(
                self,
                "Published",
                f"Successfully published to:\n{file_path}"
            )
            
            self.accept()
            
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Publishing failed:\n{str(e)}")


class UnpublishDialog(QDialog):
    """Dialog to confirm unpublishing a locked story."""
    
    def __init__(self, story: Story, parent=None) -> None:
        super().__init__(parent)
        self.story = story
        
        self.setWindowTitle("Unpublish Story")
        self.setMinimumWidth(400)
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Warning message
        warning = QLabel(
            f"<h3>Unpublish '{self.story.title}'?</h3>"
            "<p>This story is currently <b>Final Published</b> and locked from editing.</p>"
            "<p>Unpublishing will:</p>"
            "<ul>"
            "<li>Revert status to <b>Draft</b></li>"
            "<li>Allow editing of chapters and content</li>"
            "<li>NOT delete any published files</li>"
            "</ul>"
            "<p>You can publish again later when ready.</p>"
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        unpublish_btn = QPushButton("Unpublish")
        unpublish_btn.setStyleSheet("background-color: #cc6600;")
        unpublish_btn.clicked.connect(self.accept)
        btn_layout.addWidget(unpublish_btn)
        
        layout.addLayout(btn_layout)
