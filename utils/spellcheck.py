"""
Spell checking support for BlueWriter editors.
Provides real-time spell checking with suggestions.
"""
import re
from functools import partial
from pathlib import Path
from typing import List, Optional, Set

from PySide6.QtWidgets import QTextEdit, QMenu, QApplication
from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QTextCursor,
    QAction, QFont
)
from PySide6.QtCore import Qt, QTimer

from spellchecker import SpellChecker


class SpellCheckHighlighter(QSyntaxHighlighter):
    """Syntax highlighter that underlines misspelled words."""
    
    def __init__(self, document, spell_checker: 'BlueWriterSpellChecker') -> None:
        super().__init__(document)
        self.spell_checker = spell_checker
        
        # Format for misspelled words - red wavy underline
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineColor(QColor(255, 0, 0))
        self.error_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        
        # Word pattern - matches words, including contractions
        self.word_pattern = re.compile(r"\b[A-Za-z][a-z]*(?:'[a-z]+)?\b")
    
    def highlightBlock(self, text: str) -> None:
        """Highlight misspelled words in the text block."""
        if not self.spell_checker.enabled:
            return
        
        for match in self.word_pattern.finditer(text):
            word = match.group()
            if not self.spell_checker.is_correct(word):
                self.setFormat(match.start(), len(word), self.error_format)


class BlueWriterSpellChecker:
    """Spell checker with custom dictionary support."""
    
    def __init__(self) -> None:
        self.spell = SpellChecker()
        self.enabled = True
        self.custom_words: Set[str] = set()
        
        # Load custom dictionary
        self.custom_dict_path = Path(__file__).parent.parent / "data" / "custom_dictionary.txt"
        self.load_custom_dictionary()
    
    def load_custom_dictionary(self) -> None:
        """Load user's custom dictionary."""
        if self.custom_dict_path.exists():
            try:
                with open(self.custom_dict_path, 'r') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word:
                            self.custom_words.add(word)
                # Add to spellchecker
                if self.custom_words:
                    self.spell.word_frequency.load_words(list(self.custom_words))
            except Exception:
                pass
    
    def save_custom_dictionary(self) -> None:
        """Save custom dictionary to file."""
        try:
            self.custom_dict_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.custom_dict_path, 'w') as f:
                for word in sorted(self.custom_words):
                    f.write(word + '\n')
        except Exception:
            pass

    def is_correct(self, word: str) -> bool:
        """Check if a word is spelled correctly."""
        word_lower = word.lower()
        
        # Check custom dictionary first
        if word_lower in self.custom_words:
            return True
        
        # Check main dictionary
        return word_lower in self.spell
    
    def get_suggestions(self, word: str, max_suggestions: int = 5) -> List[str]:
        """Get spelling suggestions for a word."""
        candidates = self.spell.candidates(word.lower())
        if candidates:
            # Sort by edit distance and return top suggestions
            return list(candidates)[:max_suggestions]
        return []
    
    def add_to_dictionary(self, word: str) -> None:
        """Add a word to the custom dictionary."""
        word_lower = word.lower()
        self.custom_words.add(word_lower)
        self.spell.word_frequency.load_words([word_lower])
        self.save_custom_dictionary()
    
    def toggle_enabled(self) -> bool:
        """Toggle spell checking on/off."""
        self.enabled = not self.enabled
        return self.enabled


class SpellCheckTextEdit(QTextEdit):
    """QTextEdit with integrated spell checking."""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        # Create spell checker (shared instance for efficiency)
        if not hasattr(SpellCheckTextEdit, '_shared_spell_checker'):
            SpellCheckTextEdit._shared_spell_checker = BlueWriterSpellChecker()
        self.spell_checker = SpellCheckTextEdit._shared_spell_checker
        
        # Create highlighter
        self.highlighter = SpellCheckHighlighter(self.document(), self.spell_checker)
        
        # Context menu support
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Track word position for replacement (start, end positions)
        self._word_start = 0
        self._word_end = 0
        
        # Delayed rehighlight for performance
        self._rehighlight_timer = QTimer(self)
        self._rehighlight_timer.setSingleShot(True)
        self._rehighlight_timer.timeout.connect(self.highlighter.rehighlight)
    
    def show_context_menu(self, pos) -> None:
        """Show context menu with spell check options."""
        # Get cursor at click position
        cursor = self.cursorForPosition(pos)
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        
        # Store positions for later use
        self._word_start = cursor.selectionStart()
        self._word_end = cursor.selectionEnd()
        
        # Create menu
        menu = self.createStandardContextMenu()
        
        if word and not self.spell_checker.is_correct(word):
            # Insert spell check options at top
            first_action = menu.actions()[0] if menu.actions() else None
            
            # Add suggestions
            suggestions = self.spell_checker.get_suggestions(word)
            if suggestions:
                menu.insertSeparator(first_action)
                for suggestion in suggestions:
                    action = QAction(suggestion, menu)
                    action.setFont(QFont("", -1, QFont.Bold))
                    # Use partial instead of lambda for reliable binding
                    action.triggered.connect(partial(self.replace_word, suggestion))
                    menu.insertAction(first_action, action)
            
            # Add to dictionary option
            menu.insertSeparator(first_action)
            add_action = QAction(f"Add '{word}' to dictionary", menu)
            add_action.triggered.connect(partial(self.add_to_dictionary, word))
            menu.insertAction(first_action, add_action)
            
            menu.insertSeparator(first_action)
        
        menu.exec(self.mapToGlobal(pos))

    def replace_word(self, replacement: str, checked: bool = False) -> None:
        """Replace the misspelled word with the suggestion."""
        if self._word_start < self._word_end:
            # Create a fresh cursor and select the word by position
            cursor = self.textCursor()
            cursor.setPosition(self._word_start)
            cursor.setPosition(self._word_end, QTextCursor.KeepAnchor)
            
            # Replace the selected text
            cursor.insertText(replacement)
            
            # Update the editor's cursor
            self.setTextCursor(cursor)
            
            # Reset positions
            self._word_start = 0
            self._word_end = 0
            
            # Trigger rehighlight
            self.schedule_rehighlight()
    
    def add_to_dictionary(self, word: str, checked: bool = False) -> None:
        """Add word to custom dictionary and refresh."""
        self.spell_checker.add_to_dictionary(word)
        self.schedule_rehighlight()
    
    def schedule_rehighlight(self) -> None:
        """Schedule a rehighlight (debounced for performance)."""
        self._rehighlight_timer.start(100)
    
    def set_spell_check_enabled(self, enabled: bool) -> None:
        """Enable or disable spell checking."""
        self.spell_checker.enabled = enabled
        self.highlighter.rehighlight()
    
    def is_spell_check_enabled(self) -> bool:
        """Check if spell checking is enabled."""
        return self.spell_checker.enabled


# Ensure utils directory has __init__.py
_init_file = Path(__file__).parent / "__init__.py"
if not _init_file.exists():
    _init_file.touch()
