"""
Find/Replace widget for BlueWriter text editors.
Provides find, find next, find previous, replace, and replace all functionality.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QLabel, QCheckBox, QFrame
)
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QTextDocument
from PySide6.QtCore import Qt, Signal


class FindReplaceWidget(QWidget):
    """A find/replace bar widget for text editors."""
    
    closed = Signal()
    
    def __init__(self, text_edit, parent=None) -> None:
        super().__init__(parent)
        self.text_edit = text_edit
        self.last_search = ""
        self.matches = []
        self.current_match_index = -1
        
        self.setup_ui()
        self.hide()  # Start hidden
    
    def setup_ui(self) -> None:
        """Set up the find/replace UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Find row
        find_row = QHBoxLayout()
        find_row.setSpacing(5)
        
        find_row.addWidget(QLabel("Find:"))
        
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Search text...")
        self.find_edit.textChanged.connect(self.on_find_text_changed)
        self.find_edit.returnPressed.connect(self.find_next)
        find_row.addWidget(self.find_edit, 1)
        
        self.match_label = QLabel("")
        self.match_label.setMinimumWidth(80)
        find_row.addWidget(self.match_label)
        
        prev_btn = QPushButton("◀ Prev")
        prev_btn.setToolTip("Find Previous (Shift+F3)")
        prev_btn.clicked.connect(self.find_previous)
        find_row.addWidget(prev_btn)
        
        next_btn = QPushButton("Next ▶")
        next_btn.setToolTip("Find Next (F3)")
        next_btn.clicked.connect(self.find_next)
        find_row.addWidget(next_btn)
        
        layout.addLayout(find_row)
        
        # Replace row
        replace_row = QHBoxLayout()
        replace_row.setSpacing(5)
        
        replace_row.addWidget(QLabel("Replace:"))
        
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replacement text...")
        self.replace_edit.returnPressed.connect(self.replace_next)
        replace_row.addWidget(self.replace_edit, 1)
        
        replace_btn = QPushButton("Replace")
        replace_btn.setToolTip("Replace current match")
        replace_btn.clicked.connect(self.replace_next)
        replace_row.addWidget(replace_btn)
        
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.setToolTip("Replace all matches")
        replace_all_btn.clicked.connect(self.replace_all)
        replace_row.addWidget(replace_all_btn)
        
        layout.addLayout(replace_row)
        
        # Options row
        options_row = QHBoxLayout()
        options_row.setSpacing(10)
        
        self.case_sensitive = QCheckBox("Case sensitive")
        self.case_sensitive.toggled.connect(self.on_options_changed)
        options_row.addWidget(self.case_sensitive)
        
        self.whole_words = QCheckBox("Whole words")
        self.whole_words.toggled.connect(self.on_options_changed)
        options_row.addWidget(self.whole_words)
        
        options_row.addStretch()
        
        close_btn = QPushButton("✕ Close")
        close_btn.setToolTip("Close find/replace (Esc)")
        close_btn.clicked.connect(self.close_widget)
        options_row.addWidget(close_btn)
        
        layout.addLayout(options_row)
        
        # Style the widget
        self.setStyleSheet("""
            FindReplaceWidget {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
            }
        """)
    
    def show_find(self) -> None:
        """Show the find/replace widget and focus the find field."""
        self.show()
        self.find_edit.setFocus()
        self.find_edit.selectAll()
        
        # If there's selected text, use it as the search term
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            # Limit to first line (in case of multi-line selection)
            if '\u2029' in selected:  # Qt paragraph separator
                selected = selected.split('\u2029')[0]
            self.find_edit.setText(selected)
            self.find_edit.selectAll()
    
    def close_widget(self) -> None:
        """Hide the widget and clear highlights."""
        self.clear_highlights()
        self.hide()
        self.text_edit.setFocus()
        self.closed.emit()
    
    def keyPressEvent(self, event) -> None:
        """Handle key presses."""
        if event.key() == Qt.Key_Escape:
            self.close_widget()
        elif event.key() == Qt.Key_F3:
            if event.modifiers() & Qt.ShiftModifier:
                self.find_previous()
            else:
                self.find_next()
        else:
            super().keyPressEvent(event)
    
    def on_find_text_changed(self, text: str) -> None:
        """Handle find text changes - update matches."""
        self.find_all_matches()
    
    def on_options_changed(self) -> None:
        """Handle option changes - re-search."""
        self.find_all_matches()
    
    def find_all_matches(self) -> None:
        """Find all matches and highlight them."""
        self.clear_highlights()
        self.matches = []
        self.current_match_index = -1
        
        search_text = self.find_edit.text()
        if not search_text:
            self.match_label.setText("")
            return
        
        # Build find flags
        flags = QTextDocument.FindFlags()
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_words.isChecked():
            flags |= QTextDocument.FindWholeWords
        
        # Find all matches
        document = self.text_edit.document()
        cursor = QTextCursor(document)
        
        while True:
            cursor = document.find(search_text, cursor, flags)
            if cursor.isNull():
                break
            self.matches.append({
                'start': cursor.selectionStart(),
                'end': cursor.selectionEnd()
            })
        
        # Update match count
        if self.matches:
            self.match_label.setText(f"0 of {len(self.matches)}")
            self.highlight_all_matches()
            # Auto-select first match
            self.find_next()
        else:
            self.match_label.setText("No matches")
            self.match_label.setStyleSheet("color: #ff6666;")
    
    def highlight_all_matches(self) -> None:
        """Highlight all matches with background color."""
        # Use extra selections for highlighting
        selections = []
        
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#444400"))  # Dark yellow
        
        for match in self.matches:
            cursor = self.text_edit.textCursor()
            cursor.setPosition(match['start'])
            cursor.setPosition(match['end'], QTextCursor.KeepAnchor)
            
            selection = self.text_edit.ExtraSelection()
            selection.cursor = cursor
            selection.format = highlight_format
            selections.append(selection)
        
        self.text_edit.setExtraSelections(selections)
    
    def clear_highlights(self) -> None:
        """Clear all match highlights."""
        self.text_edit.setExtraSelections([])
    
    def find_next(self) -> None:
        """Move to next match."""
        if not self.matches:
            return
        
        self.current_match_index += 1
        if self.current_match_index >= len(self.matches):
            self.current_match_index = 0  # Wrap around
        
        self.go_to_current_match()
    
    def find_previous(self) -> None:
        """Move to previous match."""
        if not self.matches:
            return
        
        self.current_match_index -= 1
        if self.current_match_index < 0:
            self.current_match_index = len(self.matches) - 1  # Wrap around
        
        self.go_to_current_match()
    
    def go_to_current_match(self) -> None:
        """Select and scroll to the current match."""
        if self.current_match_index < 0 or self.current_match_index >= len(self.matches):
            return
        
        match = self.matches[self.current_match_index]
        
        # Select the match in the editor
        cursor = self.text_edit.textCursor()
        cursor.setPosition(match['start'])
        cursor.setPosition(match['end'], QTextCursor.KeepAnchor)
        self.text_edit.setTextCursor(cursor)
        
        # Ensure it's visible
        self.text_edit.ensureCursorVisible()
        
        # Update match label
        self.match_label.setText(f"{self.current_match_index + 1} of {len(self.matches)}")
        self.match_label.setStyleSheet("color: #66ff66;")
        
        # Update highlights to show current match differently
        self.update_highlight_for_current()
    
    def update_highlight_for_current(self) -> None:
        """Update highlights to emphasize current match."""
        selections = []
        
        for i, match in enumerate(self.matches):
            cursor = self.text_edit.textCursor()
            cursor.setPosition(match['start'])
            cursor.setPosition(match['end'], QTextCursor.KeepAnchor)
            
            selection = self.text_edit.ExtraSelection()
            selection.cursor = cursor
            
            if i == self.current_match_index:
                # Current match - bright highlight
                fmt = QTextCharFormat()
                fmt.setBackground(QColor("#888800"))  # Brighter yellow
                fmt.setForeground(QColor("#ffffff"))
                selection.format = fmt
            else:
                # Other matches - dim highlight
                fmt = QTextCharFormat()
                fmt.setBackground(QColor("#444400"))
                selection.format = fmt
            
            selections.append(selection)
        
        self.text_edit.setExtraSelections(selections)
    
    def replace_next(self) -> None:
        """Replace current match and move to next."""
        if self.current_match_index < 0 or not self.matches:
            # No current match, try to find first
            self.find_next()
            return
        
        replace_text = self.replace_edit.text()
        
        # Get current match
        match = self.matches[self.current_match_index]
        
        # Replace it
        cursor = self.text_edit.textCursor()
        cursor.setPosition(match['start'])
        cursor.setPosition(match['end'], QTextCursor.KeepAnchor)
        cursor.insertText(replace_text)
        
        # Re-find all matches (positions have changed)
        self.find_all_matches()
    
    def replace_all(self) -> None:
        """Replace all matches."""
        if not self.matches:
            return
        
        search_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        
        if not search_text:
            return
        
        # Count for message
        count = len(self.matches)
        
        # Replace from end to start to preserve positions
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()  # Group for undo
        
        for match in reversed(self.matches):
            cursor.setPosition(match['start'])
            cursor.setPosition(match['end'], QTextCursor.KeepAnchor)
            cursor.insertText(replace_text)
        
        cursor.endEditBlock()
        
        # Clear matches and update
        self.matches = []
        self.current_match_index = -1
        self.clear_highlights()
        self.match_label.setText(f"Replaced {count}")
        self.match_label.setStyleSheet("color: #66ff66;")
