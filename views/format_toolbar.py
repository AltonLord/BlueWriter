"""
Formatting toolbar for BlueWriter chapter editor.
Provides text formatting capabilities for chapter content.
"""
from PySide6.QtWidgets import (QToolBar, QAction, QToolButton, QWidget, 
                             QComboBox, QSizePolicy)
from PySide6.QtGui import (QFont, QTextCharFormat, QTextCursor, QFontDatabase,
                          QTextListFormat, QKeySequence)
from PySide6.QtCore import Qt


class FormatToolbar(QToolBar):
    """Toolbar providing text formatting options for chapter editing."""
    
    def __init__(self, parent=None) -> None:
        """Initialize the formatting toolbar.
        
        Args:
            parent: Parent widget for the toolbar.
        """
        super().__init__(parent)
        self.setObjectName("format_toolbar")
        self.setWindowTitle("Formatting Toolbar")
        
        # Create font size combo box
        self.font_size_combo = QComboBox(self)
        self.font_size_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.font_size_combo.setEditable(True)
        self.font_size_combo.setInsertPolicy(QComboBox.NoInsert)
        
        # Add common font sizes
        font_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        for size in font_sizes:
            self.font_size_combo.addItem(str(size))
        
        # Add the combo box to toolbar
        self.addWidget(self.font_size_combo)
        
        # Add separator
        self.addSeparator()
        
        # Create text formatting actions
        self.bold_action = QAction("Bold", self)
        self.bold_action.setCheckable(True)
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.addAction(self.bold_action)
        
        self.italic_action = QAction("Italic", self)
        self.italic_action.setCheckable(True)
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.addAction(self.italic_action)
        
        self.underline_action = QAction("Underline", self)
        self.underline_action.setCheckable(True)
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.addAction(self.underline_action)
        
        # Add separator
        self.addSeparator()
        
        # Alignment actions
        self.align_left_action = QAction("Align Left", self)
        self.align_left_action.setCheckable(True)
        self.addAction(self.align_left_action)
        
        self.align_center_action = QAction("Align Center", self)
        self.align_center_action.setCheckable(True)
        self.addAction(self.align_center_action)
        
        self.align_right_action = QAction("Align Right", self)
        self.align_right_action.setCheckable(True)
        self.addAction(self.align_right_action)
        
        # Add separator
        self.addSeparator()
        
        # List actions
        self.bullet_list_action = QAction("Bullet List", self)
        self.bullet_list_action.setCheckable(True)
        self.addAction(self.bullet_list_action)
        
        self.numbered_list_action = QAction("Numbered List", self)
        self.numbered_list_action.setCheckable(True)
        self.addAction(self.numbered_list_action)
        
        # Connect signals
        self.bold_action.triggered.connect(self.toggle_bold)
        self.italic_action.triggered.connect(self.toggle_italic)
        self.underline_action.triggered.connect(self.toggle_underline)
        self.align_left_action.triggered.connect(lambda: self.set_alignment(Qt.AlignLeft))
        self.align_center_action.triggered.connect(lambda: self.set_alignment(Qt.AlignCenter))
        self.align_right_action.triggered.connect(lambda: self.set_alignment(Qt.AlignRight))
        self.bullet_list_action.triggered.connect(self.toggle_bullet_list)
        self.numbered_list_action.triggered.connect(self.toggle_numbered_list)
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        
        # Set initial state
        self.update_formatting_buttons()
    
    def set_editor(self, text_edit) -> None:
        """Set the QTextEdit widget to apply formatting to.
        
        Args:
            text_edit: QTextEdit widget to format.
        """
        self.text_edit = text_edit
        # Connect text edit signals for real-time button updates
        if hasattr(self.text_edit, 'cursorPositionChanged'):
            self.text_edit.cursorPositionChanged.connect(self.update_formatting_buttons)
    
    def toggle_bold(self) -> None:
        """Toggle bold formatting."""
        if not self.text_edit:
            return
            
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        font = char_format.font()
        font.setBold(not font.bold())
        char_format.setFont(font)
        cursor.setCharFormat(char_format)
        self.text_edit.setTextCursor(cursor)
    
    def toggle_italic(self) -> None:
        """Toggle italic formatting."""
        if not self.text_edit:
            return
            
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        font = char_format.font()
        font.setItalic(not font.italic())
        char_format.setFont(font)
        cursor.setCharFormat(char_format)
        self.text_edit.setTextCursor(cursor)
    
    def toggle_underline(self) -> None:
        """Toggle underline formatting."""
        if not self.text_edit:
            return
            
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        font = char_format.font()
        font.setUnderline(not font.underline())
        char_format.setFont(font)
        cursor.setCharFormat(char_format)
        self.text_edit.setTextCursor(cursor)
    
    def set_alignment(self, alignment) -> None:
        """Set text alignment."""
        if not self.text_edit:
            return
            
        cursor = self.text_edit.textCursor()
        block_format = cursor.blockFormat()
        block_format.setAlignment(alignment)
        cursor.setBlockFormat(block_format)
        self.text_edit.setTextCursor(cursor)
    
    def toggle_bullet_list(self) -> None:
        """Toggle bullet list formatting."""
        if not self.text_edit:
            return
            
        cursor = self.text_edit.textCursor()
        block_format = cursor.blockFormat()
        
        # Check if current line is part of a list
        if block_format.objectType() == QTextListFormat.List:
            # Remove list formatting
            cursor.beginEditBlock()
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.setBlockFormat(QTextCharFormat())
            cursor.endEditBlock()
        else:
            # Create bullet list
            cursor.beginEditBlock()
            cursor.select(QTextCursor.BlockUnderCursor)
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.ListDisc)
            cursor.createList(list_format)
            cursor.endEditBlock()
    
    def toggle_numbered_list(self) -> None:
        """Toggle numbered list formatting."""
        if not self.text_edit:
            return
            
        cursor = self.text_edit.textCursor()
        block_format = cursor.blockFormat()
        
        # Check if current line is part of a list
        if block_format.objectType() == QTextListFormat.List:
            # Remove list formatting
            cursor.beginEditBlock()
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.setBlockFormat(QTextCharFormat())
            cursor.endEditBlock()
        else:
            # Create numbered list
            cursor.beginEditBlock()
            cursor.select(QTextCursor.BlockUnderCursor)
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.ListDecimal)
            cursor.createList(list_format)
            cursor.endEditBlock()
    
    def change_font_size(self, size_str) -> None:
        """Change font size."""
        if not self.text_edit or not size_str.isdigit():
            return
            
        size = int(size_str)
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        font = char_format.font()
        font.setPointSize(size)
        char_format.setFont(font)
        cursor.setCharFormat(char_format)
        self.text_edit.setTextCursor(cursor)
    
    def update_formatting_buttons(self) -> None:
        """Update the state of formatting buttons based on current cursor position."""
        if not self.text_edit:
            return
            
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        font = char_format.font()
        
        # Update bold button
        self.bold_action.setChecked(font.bold())
        
        # Update italic button
        self.italic_action.setChecked(font.italic())
        
        # Update underline button
        self.underline_action.setChecked(font.underline())
        
        # Update font size
        self.font_size_combo.setCurrentText(str(font.pointSize()))
