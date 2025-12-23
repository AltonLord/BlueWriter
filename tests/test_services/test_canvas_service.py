"""
Unit tests for CanvasService.

Tests canvas viewport state management and event emission.
"""
import pytest
from events.events import CanvasPanned, CanvasZoomed


class TestCanvasService:
    """Test cases for CanvasService."""
    
    # =========================================================================
    # View State Tests
    # =========================================================================
    
    def test_get_view_default(self, canvas_service):
        """Test getting default view state."""
        view = canvas_service.get_view(story_id=1)
        
        assert view.pan_x == 0.0
        assert view.pan_y == 0.0
        assert view.zoom == 1.0
    
    def test_set_pan(self, canvas_service, event_recorder):
        """Test setting pan position."""
        view = canvas_service.set_pan(story_id=1, x=100.0, y=200.0)
        
        assert view.pan_x == 100.0
        assert view.pan_y == 200.0
        
        assert event_recorder.has_event(CanvasPanned)
    
    def test_set_pan_negative(self, canvas_service):
        """Test setting negative pan position."""
        view = canvas_service.set_pan(story_id=1, x=-50.0, y=-100.0)
        
        assert view.pan_x == -50.0
        assert view.pan_y == -100.0
    
    def test_set_zoom(self, canvas_service, event_recorder):
        """Test setting zoom level."""
        view = canvas_service.set_zoom(story_id=1, zoom=1.5)
        
        assert view.zoom == 1.5
        
        assert event_recorder.has_event(CanvasZoomed)
    
    def test_set_zoom_clamped_min(self, canvas_service):
        """Test that zoom is clamped to minimum."""
        view = canvas_service.set_zoom(story_id=1, zoom=0.01)
        assert view.zoom >= 0.1  # Minimum
    
    def test_set_zoom_clamped_max(self, canvas_service):
        """Test that zoom is clamped to maximum."""
        view = canvas_service.set_zoom(story_id=1, zoom=10.0)
        assert view.zoom <= 3.0  # Maximum
    
    def test_independent_story_views(self, canvas_service):
        """Test that each story has independent view state."""
        canvas_service.set_pan(story_id=1, x=100.0, y=100.0)
        canvas_service.set_pan(story_id=2, x=200.0, y=200.0)
        
        view1 = canvas_service.get_view(story_id=1)
        view2 = canvas_service.get_view(story_id=2)
        
        assert view1.pan_x == 100.0
        assert view2.pan_x == 200.0
    
    # =========================================================================
    # Focus and Fit Tests
    # =========================================================================
    
    def test_focus_chapter(self, canvas_service, event_recorder):
        """Test focusing on a chapter position."""
        event_recorder.clear()
        
        view = canvas_service.focus_chapter(
            story_id=1,
            chapter_x=500.0,
            chapter_y=300.0
        )
        
        # View should be centered on the chapter
        assert view is not None
        assert event_recorder.has_event(CanvasPanned)
    
    def test_fit_all_with_chapters(self, canvas_service, event_recorder):
        """Test fitting all chapters in view."""
        chapter_positions = [
            (0, 0),
            (500, 0),
            (0, 400),
            (500, 400)
        ]
        event_recorder.clear()
        
        view = canvas_service.fit_all(
            story_id=1,
            chapter_positions=chapter_positions
        )
        
        # View should be adjusted to show all chapters
        assert view is not None
        assert event_recorder.has_event(CanvasZoomed)
    
    def test_fit_all_empty(self, canvas_service):
        """Test fit_all with no chapters resets to default."""
        # First set a non-default view
        canvas_service.set_pan(story_id=1, x=500.0, y=500.0)
        canvas_service.set_zoom(story_id=1, zoom=2.0)
        
        # Fit with no chapters should reset
        view = canvas_service.fit_all(story_id=1, chapter_positions=None)
        
        assert view.pan_x == 0.0
        assert view.pan_y == 0.0
        assert view.zoom == 1.0
    
    # =========================================================================
    # Reset Tests
    # =========================================================================
    
    def test_reset_view(self, canvas_service):
        """Test resetting view to defaults."""
        canvas_service.set_pan(story_id=1, x=500.0, y=500.0)
        canvas_service.set_zoom(story_id=1, zoom=2.0)
        
        view = canvas_service.reset_view(story_id=1)
        
        assert view.pan_x == 0.0
        assert view.pan_y == 0.0
        assert view.zoom == 1.0
    
    # =========================================================================
    # Clear Tests
    # =========================================================================
    
    def test_clear_story(self, canvas_service):
        """Test clearing a story's view state."""
        canvas_service.set_pan(story_id=1, x=500.0, y=500.0)
        
        canvas_service.clear_story(story_id=1)
        
        # Should get default view after clear
        view = canvas_service.get_view(story_id=1)
        assert view.pan_x == 0.0
    
    def test_clear_all(self, canvas_service):
        """Test clearing all view states."""
        canvas_service.set_pan(story_id=1, x=100.0, y=100.0)
        canvas_service.set_pan(story_id=2, x=200.0, y=200.0)
        
        canvas_service.clear_all()
        
        view1 = canvas_service.get_view(story_id=1)
        view2 = canvas_service.get_view(story_id=2)
        
        assert view1.pan_x == 0.0
        assert view2.pan_x == 0.0
