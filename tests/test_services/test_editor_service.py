"""
Unit tests for EditorService.

Tests editor tracking and modified state management.
"""
import pytest
from events.events import EditorStateChanged, EditorModifiedChanged


class TestEditorService:
    """Test cases for EditorService."""
    
    # =========================================================================
    # Registration Tests
    # =========================================================================
    
    def test_register_editor_opened(self, editor_service, event_recorder):
        """Test registering an editor as open."""
        editor_service.register_editor_opened("chapter", item_id=1)
        
        assert editor_service.is_editor_open("chapter", 1)
        assert not editor_service.is_editor_modified("chapter", 1)
    
    def test_register_editor_opened_emits_event(self, editor_service, event_recorder):
        """Test that opening an editor emits event."""
        editor_service.register_editor_opened("chapter", item_id=1)
        
        # Check for the correct event type
        events = [e for e in event_recorder.get_events() 
                  if isinstance(e, EditorStateChanged)]
        assert len(events) >= 1
        # Find the one for our editor
        matching = [e for e in events if e.item_id == 1 and e.is_open]
        assert len(matching) == 1
    
    def test_register_editor_closed(self, editor_service, event_recorder):
        """Test registering an editor as closed."""
        editor_service.register_editor_opened("chapter", item_id=1)
        event_recorder.clear()
        
        editor_service.register_editor_closed("chapter", item_id=1)
        
        assert not editor_service.is_editor_open("chapter", 1)
    
    def test_register_invalid_editor_type_fails(self, editor_service):
        """Test that invalid editor type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid editor type"):
            editor_service.register_editor_opened("invalid", item_id=1)
    
    def test_register_duplicate_open_ignored(self, editor_service, event_recorder):
        """Test that opening an already-open editor is ignored."""
        editor_service.register_editor_opened("chapter", item_id=1)
        event_recorder.clear()
        
        # Open again - should be ignored
        editor_service.register_editor_opened("chapter", item_id=1)
        
        # Should not emit another event
        events = [e for e in event_recorder.get_events() 
                  if isinstance(e, EditorStateChanged)]
        assert len(events) == 0
    
    # =========================================================================
    # Modified State Tests
    # =========================================================================
    
    def test_set_editor_modified(self, editor_service, event_recorder):
        """Test setting an editor as modified."""
        editor_service.register_editor_opened("chapter", item_id=1)
        event_recorder.clear()
        
        editor_service.set_editor_modified("chapter", 1, modified=True)
        
        assert editor_service.is_editor_modified("chapter", 1)
    
    def test_set_editor_modified_emits_event(self, editor_service, event_recorder):
        """Test that modifying an editor emits event."""
        editor_service.register_editor_opened("chapter", item_id=1)
        event_recorder.clear()
        
        editor_service.set_editor_modified("chapter", 1, modified=True)
        
        events = [e for e in event_recorder.get_events() 
                  if isinstance(e, EditorModifiedChanged)]
        assert len(events) == 1
        assert events[0].is_modified is True
    
    def test_set_editor_unmodified(self, editor_service):
        """Test setting an editor as not modified."""
        editor_service.register_editor_opened("chapter", item_id=1)
        editor_service.set_editor_modified("chapter", 1, modified=True)
        
        editor_service.set_editor_modified("chapter", 1, modified=False)
        
        assert not editor_service.is_editor_modified("chapter", 1)
    
    def test_set_modified_same_state_no_event(self, editor_service, event_recorder):
        """Test that setting same modified state doesn't emit event."""
        editor_service.register_editor_opened("chapter", item_id=1)
        editor_service.set_editor_modified("chapter", 1, modified=True)
        event_recorder.clear()
        
        # Set to same state
        editor_service.set_editor_modified("chapter", 1, modified=True)
        
        events = [e for e in event_recorder.get_events() 
                  if isinstance(e, EditorModifiedChanged)]
        assert len(events) == 0
    
    # =========================================================================
    # List Tests
    # =========================================================================
    
    def test_list_open_editors_empty(self, editor_service):
        """Test listing editors when none are open."""
        editors = editor_service.list_open_editors()
        assert editors == []
    
    def test_list_open_editors(self, editor_service):
        """Test listing multiple open editors."""
        editor_service.register_editor_opened("chapter", item_id=1)
        editor_service.register_editor_opened("chapter", item_id=2)
        editor_service.register_editor_opened("encyclopedia", item_id=3)
        
        editors = editor_service.list_open_editors()
        
        assert len(editors) == 3
    
    def test_get_modified_editors(self, editor_service):
        """Test getting only modified editors."""
        editor_service.register_editor_opened("chapter", item_id=1)
        editor_service.register_editor_opened("chapter", item_id=2)
        editor_service.register_editor_opened("encyclopedia", item_id=3)
        
        editor_service.set_editor_modified("chapter", 1, modified=True)
        editor_service.set_editor_modified("encyclopedia", 3, modified=True)
        
        modified = editor_service.get_modified_editors()
        
        assert len(modified) == 2
        item_ids = [e.item_id for e in modified]
        assert 1 in item_ids
        assert 3 in item_ids
        assert 2 not in item_ids
    
    # =========================================================================
    # Has Unsaved Changes Tests
    # =========================================================================
    
    def test_has_unsaved_changes_false(self, editor_service):
        """Test has_unsaved_changes when no editors modified."""
        editor_service.register_editor_opened("chapter", item_id=1)
        
        assert not editor_service.has_unsaved_changes()
    
    def test_has_unsaved_changes_true(self, editor_service):
        """Test has_unsaved_changes when editors are modified."""
        editor_service.register_editor_opened("chapter", item_id=1)
        editor_service.set_editor_modified("chapter", 1, modified=True)
        
        assert editor_service.has_unsaved_changes()
    
    # =========================================================================
    # Clear Tests
    # =========================================================================
    
    def test_clear_all(self, editor_service):
        """Test clearing all editors."""
        editor_service.register_editor_opened("chapter", item_id=1)
        editor_service.register_editor_opened("encyclopedia", item_id=2)
        
        editor_service.clear_all()
        
        assert len(editor_service.list_open_editors()) == 0
    
    # =========================================================================
    # Editor Type Tests
    # =========================================================================
    
    def test_chapter_and_encyclopedia_separate(self, editor_service):
        """Test that chapter and encyclopedia editors are tracked separately."""
        # Same item_id but different types
        editor_service.register_editor_opened("chapter", item_id=1)
        editor_service.register_editor_opened("encyclopedia", item_id=1)
        
        editor_service.set_editor_modified("chapter", 1, modified=True)
        
        assert editor_service.is_editor_modified("chapter", 1)
        assert not editor_service.is_editor_modified("encyclopedia", 1)
