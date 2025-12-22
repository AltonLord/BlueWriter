"""
Auto-save system for BlueWriter chapter editor.
Automatically saves chapter content at regular intervals.
"""
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor
import time


class AutoSaveSystem:
    """Manages automatic saving of chapter content."""
    
    # Signal emitted when a save operation completes
    save_completed = Signal(bool)
    
    def __init__(self, parent=None) -> None:
        """Initialize the auto-save system.
        
        Args:
            parent: Parent widget for the system.
        """
        self.parent = parent
        self.timer = QTimer()
        self.timer.timeout.connect(self._auto_save)
        self.is_active = False
        self.save_interval = 30000  # Default 30 seconds in milliseconds
        self.last_save_time = 0
        self.save_in_progress = False
        
        # Create status indicator widget
        self.status_widget = QWidget()
        layout = QHBoxLayout(self.status_widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.status_label = QLabel("Auto-save: OFF")
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        # Add a small indicator dot
        self.indicator_dot = QLabel("●")
        self.indicator_dot.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.indicator_dot)
        
        layout.addStretch()
        
    def start_auto_save(self, interval_ms: int = 30000) -> None:
        """Start the auto-save timer.
        
        Args:
            interval_ms: Auto-save interval in milliseconds (default 30 seconds).
        """
        self.save_interval = interval_ms
        self.timer.start(interval_ms)
        self.is_active = True
        self._update_status_display()
        
    def stop_auto_save(self) -> None:
        """Stop the auto-save timer."""
        self.timer.stop()
        self.is_active = False
        self._update_status_display()
        
    def _auto_save(self) -> None:
        """Perform auto-save operation.
        
        This method is called by the QTimer and should not be called directly.
        """
        if self.save_in_progress:
            return
            
        # Check if enough time has passed since last save
        current_time = int(time.time())
        if current_time - self.last_save_time < self.save_interval // 1000:
            return
            
        self.save_in_progress = True
        try:
            # In a real implementation, this would save the current chapter
            # For now, we'll just simulate the save operation
            # This is where we'd call the model's save method or database operations
            
            # Simulate a save operation
            import time
            time.sleep(0.1)  # Simulate save delay
            
            self.last_save_time = current_time
            self.save_completed.emit(True)
            
        except Exception as e:
            # Handle save errors gracefully
            print(f"Auto-save failed: {e}")
            self.save_completed.emit(False)
        finally:
            self.save_in_progress = False
            
    def set_save_interval(self, interval_ms: int) -> None:
        """Set the auto-save interval.
        
        Args:
            interval_ms: New interval in milliseconds.
        """
        self.save_interval = interval_ms
        if self.is_active:
            self.timer.stop()
            self.timer.start(interval_ms)
            
    def _update_status_display(self) -> None:
        """Update the status indicator display."""
        if self.is_active:
            self.status_label.setText("Auto-save: ON")
            self.status_label.setStyleSheet("color: green;")
            self.indicator_dot.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("Auto-save: OFF")
            self.status_label.setStyleSheet("color: red;")
            self.indicator_dot.setStyleSheet("color: red; font-weight: bold;")
            
    def is_enabled(self) -> bool:
        """Check if auto-save is currently enabled.
        
        Returns:
            True if auto-save is active, False otherwise.
        """
        return self.is_active
        
    def get_status_widget(self) -> QWidget:
        """Get the status indicator widget for embedding in UI.
        
        Returns:
            QWidget containing the status display.
        """
        return self.status_widget


class AutoSaveManager:
    """Manages auto-save functionality for the entire application."""
    
    def __init__(self) -> None:
        """Initialize the auto-save manager."""
        self.systems = {}
        
    def register_system(self, name: str, system: AutoSaveSystem) -> None:
        """Register an auto-save system.
        
        Args:
            name: Name identifier for the system.
            system: AutoSaveSystem instance to register.
        """
        self.systems[name] = system
        
    def start_all(self, interval_ms: int = 30000) -> None:
        """Start all registered auto-save systems.
        
        Args:
            interval_ms: Default interval in milliseconds.
        """
        for system in self.systems.values():
            system.start_auto_save(interval_ms)
            
    def stop_all(self) -> None:
        """Stop all registered auto-save systems."""
        for system in self.systems.values():
            system.stop_auto_save
            
    def set_interval(self, interval_ms: int) -> None:
        """Set the same interval for all systems.
        
        Args:
            interval_ms: New interval in milliseconds.
        """
        for system in self.systems.values():
            system.set_save_interval(interval_ms)
