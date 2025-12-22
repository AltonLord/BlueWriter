"""
Editor service for BlueWriter.

Tracks which editors are open and their modified (dirty) state.
This is a stateful service - state is stored in memory, not database.
Emits events for state changes that UI can subscribe to.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from events.event_bus import EventBus
from events.events import EditorStateChanged, EditorModifiedChanged


# Valid editor types
EDITOR_TYPE_CHAPTER = "chapter"
EDITOR_TYPE_ENCYCLOPEDIA = "encyclopedia"
VALID_EDITOR_TYPES = {EDITOR_TYPE_CHAPTER, EDITOR_TYPE_ENCYCLOPEDIA}


@dataclass
class OpenEditorDTO:
    """Data transfer object for an open editor.
    
    Represents the state of an open editor in the UI.
    """
    editor_type: str  # "chapter" or "encyclopedia"
    item_id: int
    is_modified: bool


class EditorService:
    """Service for tracking open editors.
    
    Tracks which chapter and encyclopedia editors are open,
    and whether they have unsaved changes. State is stored in
    memory and does not persist to database.
    
    Note: Unlike other services, this does not inherit from BaseService
    since it doesn't need database access.
    
    Example:
        event_bus = EventBus()
        service = EditorService(event_bus)
        
        # Register an editor as open
        service.register_editor_opened("chapter", chapter_id=5)
        
        # Mark as modified
        service.set_editor_modified("chapter", 5, modified=True)
        
        # Check if any editors have unsaved changes
        if service.has_unsaved_changes():
            # Prompt to save
            pass
    """
    
    def __init__(self, event_bus: EventBus) -> None:
        """Initialize the editor service.
        
        Args:
            event_bus: EventBus for publishing events
        """
        self.event_bus = event_bus
        # Key: (editor_type, item_id), Value: is_modified
        self._open_editors: Dict[Tuple[str, int], bool] = {}
    
    def _make_key(self, editor_type: str, item_id: int) -> Tuple[str, int]:
        """Create a dictionary key for an editor.
        
        Args:
            editor_type: Type of editor ("chapter" or "encyclopedia")
            item_id: ID of the item being edited
            
        Returns:
            Tuple key for the editor
            
        Raises:
            ValueError: If editor_type is invalid
        """
        if editor_type not in VALID_EDITOR_TYPES:
            raise ValueError(
                f"Invalid editor type: {editor_type}. "
                f"Must be one of: {VALID_EDITOR_TYPES}"
            )
        return (editor_type, item_id)
    
    def list_open_editors(self) -> List[OpenEditorDTO]:
        """Get all open editors.
        
        Returns:
            List of OpenEditorDTO objects for all open editors
        """
        return [
            OpenEditorDTO(
                editor_type=key[0],
                item_id=key[1],
                is_modified=is_modified,
            )
            for key, is_modified in self._open_editors.items()
        ]
    
    def register_editor_opened(self, editor_type: str, item_id: int) -> None:
        """Register that an editor has been opened.
        
        Args:
            editor_type: Type of editor ("chapter" or "encyclopedia")
            item_id: ID of the item being edited
        """
        key = self._make_key(editor_type, item_id)
        
        if key not in self._open_editors:
            self._open_editors[key] = False  # Not modified initially
            
            # Emit event
            self.event_bus.publish(EditorStateChanged(
                editor_type=editor_type,
                item_id=item_id,
                is_open=True,
            ))
    
    def register_editor_closed(self, editor_type: str, item_id: int) -> None:
        """Register that an editor has been closed.
        
        Args:
            editor_type: Type of editor ("chapter" or "encyclopedia")
            item_id: ID of the item being edited
        """
        key = self._make_key(editor_type, item_id)
        
        if key in self._open_editors:
            del self._open_editors[key]
            
            # Emit event
            self.event_bus.publish(EditorStateChanged(
                editor_type=editor_type,
                item_id=item_id,
                is_open=False,
            ))
    
    def set_editor_modified(
        self,
        editor_type: str,
        item_id: int,
        modified: bool,
    ) -> None:
        """Set an editor's modified (dirty) state.
        
        Args:
            editor_type: Type of editor ("chapter" or "encyclopedia")
            item_id: ID of the item being edited
            modified: Whether the editor has unsaved changes
        """
        key = self._make_key(editor_type, item_id)
        
        if key in self._open_editors:
            old_modified = self._open_editors[key]
            if old_modified != modified:
                self._open_editors[key] = modified
                
                # Emit event
                self.event_bus.publish(EditorModifiedChanged(
                    editor_type=editor_type,
                    item_id=item_id,
                    is_modified=modified,
                ))
    
    def is_editor_open(self, editor_type: str, item_id: int) -> bool:
        """Check if an editor is currently open.
        
        Args:
            editor_type: Type of editor ("chapter" or "encyclopedia")
            item_id: ID of the item being edited
            
        Returns:
            True if editor is open, False otherwise
        """
        key = self._make_key(editor_type, item_id)
        return key in self._open_editors
    
    def is_editor_modified(self, editor_type: str, item_id: int) -> bool:
        """Check if an editor has unsaved changes.
        
        Args:
            editor_type: Type of editor ("chapter" or "encyclopedia")
            item_id: ID of the item being edited
            
        Returns:
            True if editor has unsaved changes, False otherwise
        """
        key = self._make_key(editor_type, item_id)
        return self._open_editors.get(key, False)
    
    def has_unsaved_changes(self) -> bool:
        """Check if any open editor has unsaved changes.
        
        Returns:
            True if any editor is modified, False otherwise
        """
        return any(self._open_editors.values())
    
    def get_modified_editors(self) -> List[OpenEditorDTO]:
        """Get all editors with unsaved changes.
        
        Returns:
            List of OpenEditorDTO objects for modified editors
        """
        return [
            OpenEditorDTO(
                editor_type=key[0],
                item_id=key[1],
                is_modified=True,
            )
            for key, is_modified in self._open_editors.items()
            if is_modified
        ]
    
    def clear_all(self) -> None:
        """Clear all tracked editors.
        
        Useful for testing or when closing the application.
        Does not emit events - use register_editor_closed for proper cleanup.
        """
        self._open_editors.clear()
