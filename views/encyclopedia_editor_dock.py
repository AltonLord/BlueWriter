"""
Dockable encyclopedia entry editor for BlueWriter.
Full-featured editor for world-building entries.
"""
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QSpinBox, QFrame, QColorDialog, QFontComboBox
)
from PySide6.QtGui import (
    QAction, QFont, QTextCharFormat, QTextCursor, QKeySequence,
    QColor, QTextBlockFormat
)
from PySide6.QtCore import Qt, Signal, QTimer

from models.encyclopedia_entry import EncyclopediaEntry, DEFAULT_CATEGORIES
from database.connection import DatabaseManager, get_default_db_path
from utils.spellcheck import SpellCheckTextEdit
from views.find_replace import FindReplaceWidget


class EncyclopediaEditorDock(QDockWidget):
    """Dockable editor widget for encyclopedia entries."""
    
    entry_saved = Signal(EncyclopediaEntry)
    entry_deleted = Signal(int)  # entry_id
    entry_closed = Signal(int)   # entry_id
    
    def __init__(self, entry: EncyclopediaEntry, parent=None) -> None:
        title = f"Entry: {entry.name}" if entry.name else "New Entry"
        super().__init__(title, parent)
        self.entry = entry
        self.is_new = entry.id is None
        self.is_modified = False
        self.main_parent = parent
        
        # Dock widget settings
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea |
            Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        self.load_entry_data()
        
        # Floating window controls
        self.topLevelChanged.connect(self.on_floating_changed)
        
        # Auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)
    
    def on_floating_changed(self, floating: bool) -> None:
        """Handle transition to/from floating state."""
        if floating:
            self.setWindowFlags(
                Qt.Window |
                Qt.WindowMinMaxButtonsHint |
                Qt.WindowCloseButtonHint
            )
            self.show()

    def setup_ui(self) -> None:
        """Set up the editor UI."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # === Header section ===
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(4)
        
        # Category and Name row
        top_row = QHBoxLayout()
        
        top_row.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(DEFAULT_CATEGORIES)
        self.category_combo.setEditable(True)
        self.category_combo.setMinimumWidth(100)
        self.category_combo.currentTextChanged.connect(self.on_content_modified)
        top_row.addWidget(self.category_combo)
        
        top_row.addSpacing(10)
        
        top_row.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Entry name...")
        self.name_edit.textChanged.connect(self.on_content_modified)
        top_row.addWidget(self.name_edit, 1)
        
        header_layout.addLayout(top_row)
        
        # Tags row
        tags_row = QHBoxLayout()
        tags_row.addWidget(QLabel("Tags:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags (e.g., protagonist, warrior, kingdom)...")
        self.tags_edit.textChanged.connect(self.on_content_modified)
        tags_row.addWidget(self.tags_edit)
        header_layout.addLayout(tags_row)
        
        layout.addWidget(header)
        
        # === Main editor (create first so toolbar can reference it) ===
        self.editor = SpellCheckTextEdit()
        self.editor.setFont(QFont("Serif", 12))
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText("Enter details about this entry...")
        self.editor.textChanged.connect(self.on_content_modified)
        self.editor.cursorPositionChanged.connect(self.update_format_buttons)
        
        # === Formatting toolbar ===
        self.toolbar = QToolBar("Formatting")
        self.toolbar.setMovable(False)
        self.setup_toolbar()
        layout.addWidget(self.toolbar)
        
        # === Find/Replace bar (hidden by default) ===
        self.find_replace = FindReplaceWidget(self.editor, self)
        layout.addWidget(self.find_replace)
        
        # Add editor to layout
        layout.addWidget(self.editor, 1)
        
        # === Status bar ===
        status_layout = QHBoxLayout()
        
        self.word_count_label = QLabel("Words: 0")
        status_layout.addWidget(self.word_count_label)
        
        status_layout.addStretch()
        
        self.modified_label = QLabel("")
        status_layout.addWidget(self.modified_label)
        
        if not self.is_new:
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("color: #cc4444;")
            delete_btn.clicked.connect(self.delete_entry)
            status_layout.addWidget(delete_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setShortcut(QKeySequence.Save)
        save_btn.clicked.connect(self.save_entry)
        status_layout.addWidget(save_btn)
        
        layout.addLayout(status_layout)
        self.setWidget(container)

    def setup_toolbar(self) -> None:
        """Set up the formatting toolbar."""
        # === Undo/Redo ===
        undo_action = QAction("↶", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setToolTip("Undo (Ctrl+Z)")
        undo_action.triggered.connect(self.editor.undo)
        self.toolbar.addAction(undo_action)
        
        redo_action = QAction("↷", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setToolTip("Redo (Ctrl+Y)")
        redo_action.triggered.connect(self.editor.redo)
        self.toolbar.addAction(redo_action)
        
        self.toolbar.addSeparator()
        
        # === Font Family ===
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Serif"))
        self.font_combo.setToolTip("Font family")
        self.font_combo.setMaximumWidth(150)
        self.font_combo.currentFontChanged.connect(self.change_font_family)
        self.toolbar.addWidget(self.font_combo)
        
        # === Font Size ===
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setToolTip("Font size")
        self.font_size_spin.valueChanged.connect(self.change_font_size)
        self.toolbar.addWidget(self.font_size_spin)
        
        self.toolbar.addSeparator()
        
        # === Basic Formatting ===
        # Bold
        self.bold_action = QAction("B", self)
        self.bold_action.setFont(QFont("", -1, QFont.Bold))
        self.bold_action.setCheckable(True)
        self.bold_action.setShortcut("Ctrl+B")
        self.bold_action.setToolTip("Bold (Ctrl+B)")
        self.bold_action.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(self.bold_action)
        
        # Italic
        self.italic_action = QAction("I", self)
        italic_font = QFont()
        italic_font.setItalic(True)
        self.italic_action.setFont(italic_font)
        self.italic_action.setCheckable(True)
        self.italic_action.setShortcut("Ctrl+I")
        self.italic_action.setToolTip("Italic (Ctrl+I)")
        self.italic_action.triggered.connect(self.toggle_italic)
        self.toolbar.addAction(self.italic_action)
        
        # Underline
        self.underline_action = QAction("U", self)
        underline_font = QFont()
        underline_font.setUnderline(True)
        self.underline_action.setFont(underline_font)
        self.underline_action.setCheckable(True)
        self.underline_action.setShortcut("Ctrl+U")
        self.underline_action.setToolTip("Underline (Ctrl+U)")
        self.underline_action.triggered.connect(self.toggle_underline)
        self.toolbar.addAction(self.underline_action)
        
        # Strikethrough
        self.strike_action = QAction("S̶", self)
        self.strike_action.setCheckable(True)
        self.strike_action.setToolTip("Strikethrough")
        self.strike_action.triggered.connect(self.toggle_strikethrough)
        self.toolbar.addAction(self.strike_action)
        
        self.toolbar.addSeparator()
        
        # === Highlight ===
        self.highlight_action = QAction("🖍", self)
        self.highlight_action.setToolTip("Highlight text")
        self.highlight_action.triggered.connect(self.apply_highlight)
        self.toolbar.addAction(self.highlight_action)
        
        self.clear_highlight_action = QAction("🖍̸", self)
        self.clear_highlight_action.setToolTip("Clear highlight")
        self.clear_highlight_action.triggered.connect(self.clear_highlight)
        self.toolbar.addAction(self.clear_highlight_action)
        
        self.toolbar.addSeparator()
        
        # === Alignment ===
        self.align_left_action = QAction("⬅", self)
        self.align_left_action.setCheckable(True)
        self.align_left_action.setChecked(True)
        self.align_left_action.setToolTip("Align Left")
        self.align_left_action.triggered.connect(lambda: self.set_alignment(Qt.AlignLeft))
        self.toolbar.addAction(self.align_left_action)
        
        self.align_center_action = QAction("⬌", self)
        self.align_center_action.setCheckable(True)
        self.align_center_action.setToolTip("Align Center")
        self.align_center_action.triggered.connect(lambda: self.set_alignment(Qt.AlignCenter))
        self.toolbar.addAction(self.align_center_action)
        
        self.align_right_action = QAction("➡", self)
        self.align_right_action.setCheckable(True)
        self.align_right_action.setToolTip("Align Right")
        self.align_right_action.triggered.connect(lambda: self.set_alignment(Qt.AlignRight))
        self.toolbar.addAction(self.align_right_action)
        
        self.align_justify_action = QAction("⬄", self)
        self.align_justify_action.setCheckable(True)
        self.align_justify_action.setToolTip("Justify")
        self.align_justify_action.triggered.connect(lambda: self.set_alignment(Qt.AlignJustify))
        self.toolbar.addAction(self.align_justify_action)
        
        self.toolbar.addSeparator()
        
        # === Heading Style ===
        self.heading_combo = QComboBox()
        self.heading_combo.addItems(["Normal", "Heading 1", "Heading 2", "Heading 3"])
        self.heading_combo.setToolTip("Paragraph style")
        self.heading_combo.currentIndexChanged.connect(self.apply_heading)
        self.toolbar.addWidget(self.heading_combo)
        
        self.toolbar.addSeparator()
        
        # === Find/Replace ===
        find_action = QAction("Find", self)
        find_action.setShortcut("Ctrl+F")
        find_action.setToolTip("Find (Ctrl+F)")
        find_action.triggered.connect(self.show_find_dialog)
        self.toolbar.addAction(find_action)
        
        self.toolbar.addSeparator()
        
        # === Focus Mode ===
        self.focus_action = QAction("⛶ Focus", self)
        self.focus_action.setShortcut("F11")
        self.focus_action.setToolTip("Focus Mode - Maximize editor (F11)")
        self.focus_action.triggered.connect(self.toggle_focus_mode)
        self.toolbar.addAction(self.focus_action)
        
        self.toolbar.addSeparator()
        
        # === Spell Check ===
        self.spell_action = QAction("✓ Spell", self)
        self.spell_action.setCheckable(True)
        self.spell_action.setChecked(True)
        self.spell_action.setToolTip("Toggle spell checking")
        self.spell_action.triggered.connect(self.toggle_spell_check)
        self.toolbar.addAction(self.spell_action)
    
    def load_entry_data(self) -> None:
        """Load entry data into the editor."""
        # Set category
        if self.entry.category:
            idx = self.category_combo.findText(self.entry.category)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            else:
                self.category_combo.setEditText(self.entry.category)
        
        self.name_edit.setText(self.entry.name or "")
        self.tags_edit.setText(self.entry.tags or "")
        self.editor.setHtml(self.entry.content or "")
        
        self.is_modified = False
        self.update_word_count()
        self.update_modified_indicator()

    def on_content_modified(self) -> None:
        """Handle content modification."""
        self.is_modified = True
        self.update_word_count()
        self.update_modified_indicator()
    
    def update_modified_indicator(self) -> None:
        """Update the modified indicator."""
        name = self.name_edit.text() or "New Entry"
        if self.is_modified:
            self.modified_label.setText("● Modified")
            self.modified_label.setStyleSheet("color: orange;")
            self.setWindowTitle(f"Entry: {name} *")
        else:
            self.modified_label.setText("✓ Saved")
            self.modified_label.setStyleSheet("color: green;")
            self.setWindowTitle(f"Entry: {name}")
    
    def update_word_count(self) -> None:
        """Update word count."""
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        self.word_count_label.setText(f"Words: {words:,}")
    
    def save_entry(self) -> None:
        """Save entry to database."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid", "Name cannot be empty.")
            return
        
        self.entry.name = name
        self.entry.category = self.category_combo.currentText().strip() or "General"
        self.entry.tags = self.tags_edit.text().strip()
        self.entry.content = self.editor.toHtml()
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                if self.is_new:
                    new_entry = EncyclopediaEntry.create(
                        db,
                        project_id=self.entry.project_id,
                        name=self.entry.name,
                        category=self.entry.category,
                        content=self.entry.content,
                        tags=self.entry.tags
                    )
                    self.entry = new_entry
                    self.is_new = False
                else:
                    self.entry.update(db)
            
            self.is_modified = False
            self.update_modified_indicator()
            self.entry_saved.emit(self.entry)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
    
    def auto_save(self) -> None:
        """Auto-save if modified."""
        if self.is_modified and self.name_edit.text().strip():
            self.save_entry()
    
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
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")

    # === Text Formatting Methods ===
    
    def toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if self.bold_action.isChecked() else QFont.Normal)
        self.merge_format(fmt)
    
    def toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italic_action.isChecked())
        self.merge_format(fmt)
    
    def toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underline_action.isChecked())
        self.merge_format(fmt)
    
    def change_font_size(self, size: int) -> None:
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self.merge_format(fmt)
    
    def change_font_family(self, font: QFont) -> None:
        """Change font family of selection."""
        fmt = QTextCharFormat()
        fmt.setFontFamilies([font.family()])
        self.merge_format(fmt)
    
    def toggle_strikethrough(self, checked: bool = False) -> None:
        """Toggle strikethrough formatting."""
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(self.strike_action.isChecked())
        self.merge_format(fmt)
    
    def apply_highlight(self, checked: bool = False) -> None:
        """Apply yellow highlight to selection."""
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FFFF00"))
        self.merge_format(fmt)
    
    def clear_highlight(self, checked: bool = False) -> None:
        """Clear highlight from selection."""
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(Qt.transparent))
        self.merge_format(fmt)
    
    def set_alignment(self, alignment) -> None:
        """Set paragraph alignment."""
        self.align_left_action.setChecked(alignment == Qt.AlignLeft)
        self.align_center_action.setChecked(alignment == Qt.AlignCenter)
        self.align_right_action.setChecked(alignment == Qt.AlignRight)
        self.align_justify_action.setChecked(alignment == Qt.AlignJustify)
        
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(alignment)
        cursor.mergeBlockFormat(block_fmt)
    
    def apply_heading(self, index: int) -> None:
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.BlockUnderCursor)
        
        fmt = QTextCharFormat()
        sizes = [12, 24, 18, 14]  # Normal, H1, H2, H3
        fmt.setFontPointSize(sizes[index])
        fmt.setFontWeight(QFont.Bold if index > 0 else QFont.Normal)
        
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)
    
    def merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
    
    def update_format_buttons(self) -> None:
        fmt = self.editor.currentCharFormat()
        self.bold_action.setChecked(fmt.fontWeight() == QFont.Bold)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())
        self.strike_action.setChecked(fmt.fontStrikeOut())
        
        self.font_size_spin.blockSignals(True)
        size = int(fmt.fontPointSize()) if fmt.fontPointSize() > 0 else 12
        self.font_size_spin.setValue(size)
        self.font_size_spin.blockSignals(False)
        
        self.font_combo.blockSignals(True)
        font_family = fmt.fontFamilies()[0] if fmt.fontFamilies() else "Serif"
        self.font_combo.setCurrentFont(QFont(font_family))
        self.font_combo.blockSignals(False)
        
        cursor = self.editor.textCursor()
        alignment = cursor.blockFormat().alignment()
        self.align_left_action.setChecked(alignment == Qt.AlignLeft or alignment == 0)
        self.align_center_action.setChecked(alignment == Qt.AlignCenter)
        self.align_right_action.setChecked(alignment == Qt.AlignRight)
        self.align_justify_action.setChecked(alignment == Qt.AlignJustify)
    
    def toggle_focus_mode(self) -> None:
        """Toggle focus/maximize mode."""
        if not self.isFloating():
            self.setFloating(True)
        
        if self.isMaximized():
            self.showNormal()
            self.focus_action.setText("⛶ Focus")
        else:
            self.showMaximized()
            self.focus_action.setText("⛶ Exit Focus")
    
    def show_find_dialog(self, checked: bool = False) -> None:
        """Show find/replace bar."""
        self.find_replace.show_find()
    
    def toggle_spell_check(self) -> None:
        """Toggle spell checking on/off."""
        enabled = self.spell_action.isChecked()
        self.editor.set_spell_check_enabled(enabled)
        self.spell_action.setText("✓ Spell" if enabled else "✗ Spell")
    
    def closeEvent(self, event) -> None:
        """Handle close - prompt to save if modified."""
        if self.is_modified:
            result = QMessageBox.question(
                self, "Unsaved Changes",
                f"Save changes to '{self.entry.name or 'New Entry'}'?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if result == QMessageBox.Save:
                self.save_entry()
                event.accept()
            elif result == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        self.auto_save_timer.stop()
        if self.entry.id:
            self.entry_closed.emit(self.entry.id)
        event.accept()
