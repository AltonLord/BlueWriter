"""
Dockable chapter editor for BlueWriter.
Full-featured text editor for writing chapter content.
"""
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QColorDialog, QMessageBox, QSpinBox, QFrame, QMainWindow,
    QFontComboBox
)
from PySide6.QtGui import (
    QAction, QFont, QTextCharFormat, QColor, QTextCursor,
    QKeySequence, QTextBlockFormat
)
from PySide6.QtCore import Qt, Signal, QTimer

from models.chapter import Chapter
from database.connection import DatabaseManager, get_default_db_path
from utils.spellcheck import SpellCheckTextEdit
from views.find_replace import FindReplaceWidget


class ChapterEditorDock(QDockWidget):
    """Dockable editor widget for chapter content."""
    
    chapter_saved = Signal(Chapter)
    chapter_closed = Signal(int)  # chapter_id
    
    def __init__(self, chapter: Chapter, parent=None) -> None:
        super().__init__(f"Chapter: {chapter.title}", parent)
        self.chapter = chapter
        self.is_modified = False
        self.main_parent = parent  # Store reference to main window
        
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
        
        # Set minimum size
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Create content
        self.setup_ui()
        self.load_chapter_data()
        
        # Connect to detect when we become floating
        self.topLevelChanged.connect(self.on_floating_changed)
        
        # Auto-save timer (save every 30 seconds if modified)
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)
    
    def on_floating_changed(self, floating: bool) -> None:
        """Handle transition to/from floating state."""
        if floating:
            # Add window controls (minimize, maximize, close) when floating
            self.setWindowFlags(
                Qt.Window |
                Qt.WindowMinMaxButtonsHint |
                Qt.WindowCloseButtonHint
            )
            self.show()  # Required after changing window flags
    
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

        # Title row
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self.on_content_modified)
        title_row.addWidget(self.title_edit)
        
        # Color picker
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(28, 28)
        self.color_btn.setToolTip("Note color")
        self.color_btn.clicked.connect(self.choose_color)
        title_row.addWidget(self.color_btn)
        header_layout.addLayout(title_row)
        
        # Summary row
        summary_row = QHBoxLayout()
        summary_row.addWidget(QLabel("Summary:"))
        self.summary_edit = QLineEdit()
        self.summary_edit.setPlaceholderText("Brief chapter summary for the sticky note...")
        self.summary_edit.textChanged.connect(self.on_content_modified)
        summary_row.addWidget(self.summary_edit)
        header_layout.addLayout(summary_row)
        
        layout.addWidget(header)
        
        # === Main editor (create first so toolbar can reference it) ===
        self.editor = SpellCheckTextEdit()
        self.editor.setFont(QFont("Serif", 12))
        self.editor.setAcceptRichText(True)
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
        layout.addWidget(self.editor, 1)  # Stretch factor 1
        
        # === Status bar ===
        status_layout = QHBoxLayout()
        
        self.word_count_label = QLabel("Words: 0")
        status_layout.addWidget(self.word_count_label)
        
        self.char_count_label = QLabel("Characters: 0")
        status_layout.addWidget(self.char_count_label)
        
        status_layout.addStretch()
        
        self.modified_label = QLabel("")
        status_layout.addWidget(self.modified_label)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setShortcut(QKeySequence.Save)
        save_btn.clicked.connect(self.save_chapter)
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
        self.highlight_action.setToolTip("Highlight text (click to apply yellow, right-click for color)")
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
        
        # === Scene Break ===
        scene_break_action = QAction("───", self)
        scene_break_action.setToolTip("Insert scene break")
        scene_break_action.triggered.connect(self.insert_scene_break)
        self.toolbar.addAction(scene_break_action)
        
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

    def load_chapter_data(self) -> None:
        """Load chapter data into the editor."""
        self.title_edit.setText(self.chapter.title or "")
        self.summary_edit.setText(self.chapter.summary or "")
        self.editor.setHtml(self.chapter.content or "")
        
        # Set color button
        color = self.chapter.color or "#FFFF88"
        self.current_color = color
        self.color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
        
        self.is_modified = False
        self.update_word_count()
        self.update_modified_indicator()
    
    def on_content_modified(self) -> None:
        """Handle content modification."""
        self.is_modified = True
        self.update_word_count()
        self.update_modified_indicator()
    
    def update_modified_indicator(self) -> None:
        """Update the modified indicator in status bar."""
        if self.is_modified:
            self.modified_label.setText("● Modified")
            self.modified_label.setStyleSheet("color: orange;")
            self.setWindowTitle(f"Chapter: {self.title_edit.text()} *")
        else:
            self.modified_label.setText("✓ Saved")
            self.modified_label.setStyleSheet("color: green;")
            self.setWindowTitle(f"Chapter: {self.title_edit.text()}")
    
    def update_word_count(self) -> None:
        """Update word and character counts."""
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"Words: {words:,}")
        self.char_count_label.setText(f"Characters: {chars:,}")
    
    def choose_color(self) -> None:
        """Open color picker for note color."""
        color = QColorDialog.getColor(QColor(self.current_color), self, "Choose Note Color")
        if color.isValid():
            self.current_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #888;")
            self.is_modified = True
            self.update_modified_indicator()
    
    def save_chapter(self) -> None:
        """Save chapter to database."""
        self.chapter.title = self.title_edit.text().strip() or "Untitled"
        self.chapter.summary = self.summary_edit.text().strip()
        self.chapter.content = self.editor.toHtml()
        self.chapter.color = self.current_color
        
        try:
            with DatabaseManager(get_default_db_path()) as db:
                self.chapter.update(db)
            
            self.is_modified = False
            self.update_modified_indicator()
            self.chapter_saved.emit(self.chapter)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
    
    def auto_save(self) -> None:
        """Auto-save if modified."""
        if self.is_modified:
            self.save_chapter()

    # === Text Formatting Methods ===
    
    def toggle_bold(self) -> None:
        """Toggle bold formatting."""
        fmt = QTextCharFormat()
        if self.bold_action.isChecked():
            fmt.setFontWeight(QFont.Bold)
        else:
            fmt.setFontWeight(QFont.Normal)
        self.merge_format(fmt)
    
    def toggle_italic(self) -> None:
        """Toggle italic formatting."""
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italic_action.isChecked())
        self.merge_format(fmt)
    
    def toggle_underline(self) -> None:
        """Toggle underline formatting."""
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underline_action.isChecked())
        self.merge_format(fmt)
    
    def change_font_size(self, size: int) -> None:
        """Change font size of selection."""
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
        fmt.setBackground(QColor("#FFFF00"))  # Yellow highlight
        self.merge_format(fmt)
    
    def clear_highlight(self, checked: bool = False) -> None:
        """Clear highlight from selection."""
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(Qt.transparent))
        self.merge_format(fmt)
    
    def set_alignment(self, alignment) -> None:
        """Set paragraph alignment."""
        # Update button states
        self.align_left_action.setChecked(alignment == Qt.AlignLeft)
        self.align_center_action.setChecked(alignment == Qt.AlignCenter)
        self.align_right_action.setChecked(alignment == Qt.AlignRight)
        self.align_justify_action.setChecked(alignment == Qt.AlignJustify)
        
        # Apply to current block
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(alignment)
        cursor.mergeBlockFormat(block_fmt)
    
    def insert_scene_break(self, checked: bool = False) -> None:
        """Insert a scene break (centered asterisks)."""
        cursor = self.editor.textCursor()
        
        # Move to end of current line
        cursor.movePosition(QTextCursor.EndOfBlock)
        
        # Insert scene break with centered alignment
        cursor.insertBlock()
        
        # Set center alignment for the break
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(Qt.AlignCenter)
        cursor.mergeBlockFormat(block_fmt)
        
        # Insert the scene break text
        cursor.insertText("* * *")
        
        # Insert new paragraph after and reset to left align
        cursor.insertBlock()
        block_fmt.setAlignment(Qt.AlignLeft)
        cursor.mergeBlockFormat(block_fmt)
        
        self.editor.setTextCursor(cursor)
        self.is_modified = True
        self.update_modified_indicator()
    
    def apply_heading(self, index: int) -> None:
        """Apply heading style to current paragraph."""
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.BlockUnderCursor)
        
        fmt = QTextCharFormat()
        if index == 0:  # Normal
            fmt.setFontPointSize(12)
            fmt.setFontWeight(QFont.Normal)
        elif index == 1:  # Heading 1
            fmt.setFontPointSize(24)
            fmt.setFontWeight(QFont.Bold)
        elif index == 2:  # Heading 2
            fmt.setFontPointSize(18)
            fmt.setFontWeight(QFont.Bold)
        elif index == 3:  # Heading 3
            fmt.setFontPointSize(14)
            fmt.setFontWeight(QFont.Bold)
        
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)
    
    def merge_format(self, fmt: QTextCharFormat) -> None:
        """Apply format to current selection or word."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)
    
    def update_format_buttons(self) -> None:
        """Update formatting buttons to reflect cursor position."""
        fmt = self.editor.currentCharFormat()
        
        # Update bold button
        self.bold_action.setChecked(fmt.fontWeight() == QFont.Bold)
        
        # Update italic button
        self.italic_action.setChecked(fmt.fontItalic())
        
        # Update underline button
        self.underline_action.setChecked(fmt.fontUnderline())
        
        # Update strikethrough button
        self.strike_action.setChecked(fmt.fontStrikeOut())
        
        # Update font size (block signals to prevent recursion)
        self.font_size_spin.blockSignals(True)
        size = int(fmt.fontPointSize()) if fmt.fontPointSize() > 0 else 12
        self.font_size_spin.setValue(size)
        self.font_size_spin.blockSignals(False)
        
        # Update font family (block signals to prevent recursion)
        self.font_combo.blockSignals(True)
        font_family = fmt.fontFamilies()[0] if fmt.fontFamilies() else "Serif"
        self.font_combo.setCurrentFont(QFont(font_family))
        self.font_combo.blockSignals(False)
        
        # Update alignment buttons
        cursor = self.editor.textCursor()
        alignment = cursor.blockFormat().alignment()
        self.align_left_action.setChecked(alignment == Qt.AlignLeft or alignment == 0)
        self.align_center_action.setChecked(alignment == Qt.AlignCenter)
        self.align_right_action.setChecked(alignment == Qt.AlignRight)
        self.align_justify_action.setChecked(alignment == Qt.AlignJustify)
    
    def show_find_dialog(self, checked: bool = False) -> None:
        """Show find/replace bar."""
        self.find_replace.show_find()
    
    def toggle_focus_mode(self) -> None:
        """Toggle focus/maximize mode."""
        if not self.isFloating():
            # First, make it float
            self.setFloating(True)
        
        # Toggle maximized state
        if self.isMaximized():
            self.showNormal()
            self.focus_action.setText("⛶ Focus")
        else:
            self.showMaximized()
            self.focus_action.setText("⛶ Exit Focus")
    
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
                f"Save changes to '{self.chapter.title}'?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if result == QMessageBox.Save:
                self.save_chapter()
                event.accept()
            elif result == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        self.auto_save_timer.stop()
        self.chapter_closed.emit(self.chapter.id)
        event.accept()
