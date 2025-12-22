"""
Integration tests for BlueWriter chapter editing components.
Tests the interaction between chapter editor, formatting toolbar, and auto-save system.
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from views.chapter_editor import ChapterEditor
from views.format_toolbar import FormatToolbar
from views.auto_save import AutoSaveSystem, AutoSaveManager
from models.chapter import Chapter


class TestChapterEditingIntegration:
    """Integration tests for chapter editing components."""
    
    def test_chapter_editor_initialization(self):
        """Test that chapter editor initializes correctly."""
        # Test creating new editor without chapter
        editor = ChapterEditor()
        assert editor is not None
        assert editor.windowTitle() == "Chapter Editor"
        
        # Test creating editor with existing chapter
        chapter = Chapter(title="Test Chapter", content="Test content")
        editor = ChapterEditor(chapter)
        assert editor.chapter == chapter
        
    def test_chapter_editor_save_new(self):
        """Test saving a new chapter through the editor."""
        editor = ChapterEditor()
        
        # Mock the save functionality
        with patch.object(editor, 'accept') as mock_accept:
            # Set up the inputs
            editor.title_input.setText("New Test Chapter")
            editor.content_editor.setPlainText("This is test content.")
            
            # Save the chapter
            editor.save_chapter()
            
            # Verify that accept was called (dialog closed)
            mock_accept.assert_called_once()
            
            # Verify chapter was created
            assert editor.chapter is not None
            assert editor.chapter.title == "New Test Chapter"
            assert editor.chapter.content == "This is test content."
            
    def test_chapter_editor_save_existing(self):
        """Test updating an existing chapter through the editor."""
        # Create initial chapter
        original_chapter = Chapter(title="Original Title", content="Original content")
        editor = ChapterEditor(original_chapter)
        
        # Modify the inputs
        editor.title_input.setText("Updated Title")
        editor.content_editor.setPlainText("Updated content")
        
        # Save the chapter
        with patch.object(editor, 'accept') as mock_accept:
            editor.save_chapter()
            
            # Verify that accept was called (dialog closed)
            mock_accept.assert_called_once()
            
            # Verify chapter was updated
            assert editor.chapter.title == "Updated Title"
            assert editor.chapter.content == "Updated content"
            
    def test_format_toolbar_integration(self):
        """Test that format toolbar can be integrated with text editor."""
        # Create a simple QTextEdit to test with
        from PySide6.QtWidgets import QTextEdit
        
        text_edit = QTextEdit()
        toolbar = FormatToolbar()
        
        # Test setting the editor
        toolbar.set_editor(text_edit)
        assert hasattr(toolbar, 'text_edit')
        assert toolbar.text_edit == text_edit
        
    def test_format_toolbar_functionality(self):
        """Test basic formatting functionality of the toolbar."""
        from PySide6.QtWidgets import QTextEdit
        
        # Create a simple text edit and toolbar
        text_edit = QTextEdit()
        toolbar = FormatToolbar()
        
        # Set up the editor
        toolbar.set_editor(text_edit)
        
        # Test that we can set some basic text
        text_edit.setPlainText("Test content")
        assert text_edit.toPlainText() == "Test content"
        
    def test_auto_save_system_initialization(self):
        """Test auto-save system initialization."""
        system = AutoSaveSystem()
        assert system is not None
        assert not system.is_active
        assert system.save_interval == 30000  # Default 30 seconds
        
    def test_auto_save_system_start_stop(self):
        """Test starting and stopping the auto-save system."""
        system = AutoSaveSystem()
        
        # Start the system
        system.start_auto_save(5000)  # 5 second interval for testing
        assert system.is_active
        
        # Stop the system
        system.stop_auto_save()
        assert not system.is_active
        
    def test_auto_save_system_status_widget(self):
        """Test that auto-save system provides a status widget."""
        system = AutoSaveSystem()
        widget = system.get_status_widget()
        assert widget is not None
        assert hasattr(widget, 'layout')
        
    def test_auto_save_manager_integration(self):
        """Test that auto-save manager can manage multiple systems."""
        manager = AutoSaveManager()
        system1 = AutoSaveSystem()
        system2 = AutoSaveSystem()
        
        # Register systems
        manager.register_system("chapter_save", system1)
        manager.register_system("story_save", system2)
        
        # Verify registration
        assert len(manager.systems) == 2
        assert "chapter_save" in manager.systems
        assert "story_save" in manager.systems
        
    def test_complete_workflow_simulation(self):
        """Test a simulated complete workflow."""
        # Create a chapter
        chapter = Chapter(title="Test Story", content="Initial content")
        
        # Create editor and simulate user interaction
        editor = ChapterEditor(chapter)
        
        # Simulate editing in the UI (this would normally happen through actual UI events)
        editor.title_input.setText("Updated Test Story")
        editor.content_editor.setPlainText("Updated content with more text.")
        
        # Save the chapter
        with patch.object(editor, 'accept') as mock_accept:
            editor.save_chapter()
            
            # Verify everything was updated correctly
            assert editor.chapter.title == "Updated Test Story"
            assert editor.chapter.content == "Updated content with more text."
            
            # Verify dialog was closed
            mock_accept.assert_called_once()


if __name__ == "__main__":
    # Run the tests if executed directly
    pytest.main([__file__, "-v"])
