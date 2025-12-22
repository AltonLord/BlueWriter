"""
Custom dictionary editor dialog for BlueWriter.
Allows users to view, add, and remove words from their custom dictionary.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit,
    QPushButton, QLabel, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt

from utils.spellcheck import BlueWriterSpellChecker, SpellCheckTextEdit


class DictionaryEditorDialog(QDialog):
    """Dialog for editing the custom spell check dictionary."""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Custom Dictionary")
        self.setMinimumSize(400, 500)
        
        # Get the shared spell checker instance
        if hasattr(SpellCheckTextEdit, '_shared_spell_checker'):
            self.spell_checker = SpellCheckTextEdit._shared_spell_checker
        else:
            self.spell_checker = BlueWriterSpellChecker()
        
        self.setup_ui()
        self.load_words()
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Words in your custom dictionary:")
        layout.addWidget(header)
        
        # Word list
        self.word_list = QListWidget()
        self.word_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.word_list.setSortingEnabled(True)
        layout.addWidget(self.word_list)
        
        # Add word section
        add_layout = QHBoxLayout()
        self.add_edit = QLineEdit()
        self.add_edit.setPlaceholderText("Add new word...")
        self.add_edit.returnPressed.connect(self.add_word)
        add_layout.addWidget(self.add_edit)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_word)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Word count
        self.count_label = QLabel()
        layout.addWidget(self.count_label)
    
    def load_words(self) -> None:
        """Load words from the custom dictionary."""
        self.word_list.clear()
        for word in sorted(self.spell_checker.custom_words):
            self.word_list.addItem(word)
        self.update_count()
    
    def update_count(self) -> None:
        """Update the word count label."""
        count = self.word_list.count()
        self.count_label.setText(f"{count} word{'s' if count != 1 else ''} in dictionary")
    
    def add_word(self) -> None:
        """Add a new word to the dictionary."""
        word = self.add_edit.text().strip().lower()
        if not word:
            return
        
        if word in self.spell_checker.custom_words:
            QMessageBox.information(self, "Already Exists", 
                f"'{word}' is already in your dictionary.")
            return
        
        self.spell_checker.add_to_dictionary(word)
        self.word_list.addItem(word)
        self.word_list.sortItems()
        self.add_edit.clear()
        self.update_count()
    
    def remove_selected(self) -> None:
        """Remove selected words from the dictionary."""
        selected = self.word_list.selectedItems()
        if not selected:
            return
        
        # Confirm removal
        count = len(selected)
        msg = f"Remove {count} word{'s' if count > 1 else ''} from dictionary?"
        result = QMessageBox.question(self, "Confirm Removal", msg,
            QMessageBox.Yes | QMessageBox.No)
        
        if result != QMessageBox.Yes:
            return
        
        # Remove words
        for item in selected:
            word = item.text()
            self.spell_checker.custom_words.discard(word)
            self.word_list.takeItem(self.word_list.row(item))
        
        # Save the dictionary
        self.spell_checker.save_custom_dictionary()
        self.update_count()
