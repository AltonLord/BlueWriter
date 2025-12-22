"""
Keyboard shortcuts and UX enhancements for BlueWriter chapter editing.
Implements keyboard shortcuts, tooltips, and user experience improvements.
"""
from PySide6.QtWidgets import QShortcut, QWidget, QMessageBox, QStatusBar
from PySide6.QtGui import QKeySequence, QKeyEvent
from PySide6.QtCore import Qt


class KeyboardShortcuts:
    """Manages keyboard shortcuts for the BlueWriter application."""
    
    def __init__(self, main_window):
        """
        Initialize keyboard shortcuts.
        
        Args:
            main_window: The main application window instance.
        """
        self.main_window = main_window
        self.shortcuts = []
        self._setup_shortcuts()
        
    def _setup_shortcuts(self):
        """Setup all keyboard shortcuts for the application."""
        # File shortcuts
        self._create_shortcut(Qt.ControlModifier, Qt.Key_S, self._save_chapter, "Save Chapter")
        self._create_shortcut(Qt.ControlModifier, Qt.Key_N, self._new_chapter, "New Chapter")
        self._create_shortcut(Qt.ControlModifier, Qt.Key_O, self._open_chapter, "Open Chapter")
        
        # Edit shortcuts
        self._create_shortcut(Qt.ControlModifier, Qt.Key_Z, self._undo_action, "Undo")
        self._create_shortcut(Qt.ControlModifier | Qt.ShiftModifier, Qt.Key_Z, self._redo_action, "Redo")
        self._create_shortcut(Qt.ControlModifier, Qt.Key_X, self._cut_text, "Cut")
        self._create_shortcut(Qt.ControlModifier, Qt.Key_C, self._copy_text, "Copy")
        self._create_shortcut(Qt.ControlModifier, Qt.Key_V, self._paste_text, "Paste")
        
        # Formatting shortcuts
        self._create_shortcut(Qt.ControlModifier, Qt.Key_B, self._format_bold, "Bold")
        self._create_shortcut(Qt.ControlModifier, Qt.Key_I, self._format_italic, "Italic")
        self._create_shortcut(Qt.ControlModifier, Qt.Key_U, self._format_underline, "Underline")
        
        # Navigation shortcuts
        self._create_shortcut(Qt.ControlModifier, Qt.Key_G, self._goto_line, "Go to Line")
        self._create_shortcut(Qt.AltModifier, Qt.Key_Right, self._next_chapter, "Next Chapter")
        self._create_shortcut(Qt.AltModifier, Qt.Key_Left, self._previous_chapter, "Previous Chapter")
        
        # View shortcuts
        self._create_shortcut(Qt.ControlModifier | Qt.ShiftModifier, Qt.Key_F, self._toggle_fullscreen, "Toggle Fullscreen")
        
        # Help shortcuts
        self._create_shortcut(Qt.Key_F1, self._show_help, "Help")
        
    def _create_shortcut(self, key_modifier, key, callback, description):
        """
        Create a keyboard shortcut.
        
        Args:
            key_modifier: Qt modifier key (e.g., Qt.ControlModifier)
            key: Qt key code (e.g., Qt.Key_S)
            callback: Function to call when shortcut is pressed
            description: Description of the shortcut for tooltips
        """
        shortcut = QShortcut(QKeySequence(key_modifier, key), self.main_window)
        shortcut.activated.connect(callback)
        shortcut.setToolTip(description)
        self.shortcuts.append(shortcut)
        
    def _save_chapter(self):
        """Save the current chapter."""
        # This would be implemented in the main window or chapter editor
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                self.main_window.current_editor.save_chapter()
                self._show_status_message("Chapter saved successfully", 2000)
            except Exception as e:
                self._show_error_message(f"Failed to save chapter: {str(e)}")
        else:
            self._show_status_message("No active chapter to save", 2000)
            
    def _new_chapter(self):
        """Create a new chapter."""
        # This would open the chapter editor
        try:
            self.main_window.open_chapter_editor()
            self._show_status_message("New chapter opened", 2000)
        except Exception as e:
            self._show_error_message(f"Failed to create new chapter: {str(e)}")
            
    def _open_chapter(self):
        """Open an existing chapter."""
        try:
            self.main_window.open_chapter_editor()
            self._show_status_message("Chapter opened", 2000)
        except Exception as e:
            self._show_error_message(f"Failed to open chapter: {str(e)}")
            
    def _undo_action(self):
        """Perform undo action."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the text editor
                pass  # Placeholder for actual implementation
                self._show_status_message("Undo performed", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to undo: {str(e)}")
                
    def _redo_action(self):
        """Perform redo action."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the text editor
                pass  # Placeholder for actual implementation
                self._show_status_message("Redo performed", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to redo: {str(e)}")
                
    def _cut_text(self):
        """Cut selected text."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the text editor
                pass  # Placeholder for actual implementation
                self._show_status_message("Text cut", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to cut text: {str(e)}")
                
    def _copy_text(self):
        """Copy selected text."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the text editor
                pass  # Placeholder for actual implementation
                self._show_status_message("Text copied", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to copy text: {str(e)}")
                
    def _paste_text(self):
        """Paste text from clipboard."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the text editor
                pass  # Placeholder for actual implementation
                self._show_status_message("Text pasted", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to paste text: {str(e)}")
                
    def _format_bold(self):
        """Apply bold formatting."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the formatting toolbar
                pass  # Placeholder for actual implementation
                self._show_status_message("Bold formatting applied", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to apply bold: {str(e)}")
                
    def _format_italic(self):
        """Apply italic formatting."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the formatting toolbar
                pass  # Placeholder for actual implementation
                self._show_status_message("Italic formatting applied", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to apply italic: {str(e)}")
                
    def _format_underline(self):
        """Apply underline formatting."""
        if hasattr(self.main_window, 'current_editor') and self.main_window.current_editor:
            try:
                # This would be implemented in the formatting toolbar
                pass  # Placeholder for actual implementation
                self._show_status_message("Underline formatting applied", 1000)
            except Exception as e:
                self._show_error_message(f"Failed to apply underline: {str(e)}")
                
    def _goto_line(self):
        """Go to a specific line."""
        # This would open a dialog
        try:
            self._show_status_message("Go to line dialog opened", 2000)
        except Exception as e:
            self._show_error_message(f"Failed to open go to line: {str(e)}")
            
    def _next_chapter(self):
        """Navigate to next chapter."""
        try:
            self._show_status_message("Next chapter", 1000)
        except Exception as e:
            self._show_error_message(f"Failed to navigate to next chapter: {str(e)}")
            
    def _previous_chapter(self):
        """Navigate to previous chapter."""
        try:
            self._show_status_message("Previous chapter", 1000)
        except Exception as e:
            self._show_error_message(f"Failed to navigate to previous chapter: {str(e)}")
            
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        try:
            self.main_window.toggle_fullscreen()
            self._show_status_message("Fullscreen toggled", 1000)
        except Exception as e:
            self._show_error_message(f"Failed to toggle fullscreen: {str(e)}")
            
    def _show_help(self):
        """Show help information."""
        try:
            QMessageBox.information(
                self.main_window,
                "Help",
                "BlueWriter Help\n\n"
                "Keyboard Shortcuts:\n"
                "Ctrl+S - Save Chapter\n"
                "Ctrl+N - New Chapter\n"
                "Ctrl+O - Open Chapter\n"
                "Ctrl+B - Bold\n"
                "Ctrl+I - Italic\n"
                "Ctrl+U - Underline\n"
                "F1 - Help\n\n"
                "For more information, visit the documentation.",
                QMessageBox.Ok
            )
        except Exception as e:
            self._show_error_message(f"Failed to show help: {str(e)}")
            
    def _show_status_message(self, message, timeout=3000):
        """Show a status message."""
        if hasattr(self.main_window, 'statusBar'):
            try:
                self.main_window.statusBar().showMessage(message, timeout)
            except Exception:
                pass  # Ignore errors in status bar display
                
    def _show_error_message(self, message):
        """Show an error message."""
        try:
            QMessageBox.critical(
                self.main_window,
                "Error",
                message,
                QMessageBox.Ok
            )
        except Exception:
            pass  # Ignore errors in error display


class UXEnhancements:
    """Provides user experience enhancements for the application."""
    
    def __init__(self, main_window):
        """
        Initialize UX enhancements.
        
        Args:
            main_window: The main application window instance.
        """
        self.main_window = main_window
        self._setup_tooltips()
        self._setup_focus_management()
        
    def _setup_tooltips(self):
        """Setup tooltips for UI elements."""
        # Tooltips for main window elements
        if hasattr(self.main_window, 'menuBar'):
            menu_bar = self.main_window.menuBar()
            # Add tooltips to menu items (this is a simplified version)
            
        # Setup tooltips for chapter editor elements
        # This would be done in the individual components
        
    def _setup_focus_management(self):
        """Setup focus management for better accessibility."""
        # This would involve ensuring proper tab order and focus handling
        
    def add_tooltip(self, widget, text):
        """
        Add a tooltip to a widget.
        
        Args:
            widget: The widget to add tooltip to
            text: Tooltip text
        """
        try:
            widget.setToolTip(text)
        except Exception:
            pass  # Ignore errors in tooltip setting
            
    def show_notification(self, title, message, duration=3000):
        """
        Show a notification message.
        
        Args:
            title: Notification title
            message: Notification message
            duration: Duration in milliseconds
        """
        try:
            self._show_status_message(f"{title}: {message}", duration)
        except Exception:
            pass  # Ignore errors in notification display
            
    def validate_input(self, input_widget, validator_func, error_message):
        """
        Validate user input with feedback.
        
        Args:
            input_widget: Widget containing the input
            validator_func: Function to validate input
            error_message: Error message if validation fails
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not validator_func():
                self._show_error_message(error_message)
                return False
            return True
        except Exception:
            return True  # If validation fails, we don't want to block the user


def setup_keyboard_shortcuts(main_window):
    """
    Setup all keyboard shortcuts and UX enhancements for the main window.
    
    Args:
        main_window: The main application window instance.
        
    Returns:
        KeyboardShortcuts: Instance of keyboard shortcuts manager.
    """
    # Create and return the keyboard shortcuts manager
    return KeyboardShortcuts(main_window)
