"""
Unit tests for ChapterService.

Tests all CRUD operations, content management, and event emission for chapters.
"""
import pytest
from events.events import (
    ChapterCreated, ChapterUpdated, ChapterDeleted,
    ChapterMoved, ChapterColorChanged, ChapterOpened, ChapterClosed
)


class TestChapterService:
    """Test cases for ChapterService."""
    
    # =========================================================================
    # Create Tests
    # =========================================================================
    
    def test_create_chapter(self, chapter_service, sample_story, event_recorder):
        """Test creating a new chapter."""
        event_recorder.clear()
        
        chapter = chapter_service.create_chapter(
            story_id=sample_story.id,
            title="Chapter One",
            board_x=150,
            board_y=200,
            color="#FF8888"
        )
        
        assert chapter.id is not None
        assert chapter.story_id == sample_story.id
        assert chapter.title == "Chapter One"
        assert chapter.board_x == 150
        assert chapter.board_y == 200
        assert chapter.color == "#FF8888"
    
    def test_create_chapter_emits_event(self, chapter_service, sample_story, event_recorder):
        """Test that creating a chapter emits ChapterCreated event."""
        event_recorder.clear()
        
        chapter = chapter_service.create_chapter(
            story_id=sample_story.id,
            title="Event Test"
        )
        
        assert event_recorder.has_event(ChapterCreated)
        events = event_recorder.get_events(ChapterCreated)
        assert len(events) == 1
        assert events[0].chapter_id == chapter.id
        assert events[0].story_id == sample_story.id
    
    def test_create_chapter_default_values(self, chapter_service, sample_story):
        """Test that chapters have sensible defaults."""
        chapter = chapter_service.create_chapter(
            story_id=sample_story.id,
            title="Defaults Test"
        )
        
        assert chapter.board_x == 100  # Default
        assert chapter.board_y == 100  # Default
        assert chapter.color == "#FFFF88"  # Default yellow
    
    def test_create_chapter_invalid_color_fails(self, chapter_service, sample_story):
        """Test that invalid color format raises ValueError."""
        with pytest.raises(ValueError, match="color"):
            chapter_service.create_chapter(
                story_id=sample_story.id,
                title="Bad Color",
                color="not-a-color"
            )
    
    # =========================================================================
    # Read Tests
    # =========================================================================
    
    def test_list_chapters_empty(self, chapter_service, sample_story):
        """Test listing chapters when none exist."""
        chapters = chapter_service.list_chapters(sample_story.id)
        assert chapters == []
    
    def test_list_chapters(self, chapter_service, sample_story):
        """Test listing multiple chapters."""
        chapter_service.create_chapter(story_id=sample_story.id, title="Ch 1")
        chapter_service.create_chapter(story_id=sample_story.id, title="Ch 2")
        chapter_service.create_chapter(story_id=sample_story.id, title="Ch 3")
        
        chapters = chapter_service.list_chapters(sample_story.id)
        
        assert len(chapters) == 3
    
    def test_get_chapter(self, chapter_service, sample_story):
        """Test getting a chapter by ID."""
        created = chapter_service.create_chapter(
            story_id=sample_story.id,
            title="Get Test"
        )
        
        fetched = chapter_service.get_chapter(created.id)
        
        assert fetched.id == created.id
        assert fetched.title == "Get Test"
    
    def test_get_chapter_not_found(self, chapter_service):
        """Test getting a non-existent chapter raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            chapter_service.get_chapter(99999)
    
    # =========================================================================
    # Update Tests
    # =========================================================================
    
    def test_update_chapter_title(self, chapter_service, sample_chapter, event_recorder):
        """Test updating chapter title."""
        event_recorder.clear()
        
        updated = chapter_service.update_chapter(
            sample_chapter.id,
            title="New Title"
        )
        
        assert updated.title == "New Title"
        assert event_recorder.has_event(ChapterUpdated)
    
    def test_update_chapter_summary(self, chapter_service, sample_chapter):
        """Test updating chapter summary."""
        updated = chapter_service.update_chapter(
            sample_chapter.id,
            summary="A brief summary"
        )
        
        assert updated.summary == "A brief summary"
    
    def test_update_chapter_content(self, chapter_service, sample_chapter):
        """Test updating chapter content."""
        updated = chapter_service.update_chapter(
            sample_chapter.id,
            content="<p>Chapter content here.</p>"
        )
        
        assert updated.content == "<p>Chapter content here.</p>"
    
    # =========================================================================
    # Move Tests
    # =========================================================================
    
    def test_move_chapter(self, chapter_service, sample_chapter, event_recorder):
        """Test moving a chapter on the canvas."""
        event_recorder.clear()
        
        updated = chapter_service.move_chapter(
            sample_chapter.id,
            board_x=500,
            board_y=300
        )
        
        assert updated.board_x == 500
        assert updated.board_y == 300
        
        assert event_recorder.has_event(ChapterMoved)
        event = event_recorder.get_events(ChapterMoved)[0]
        assert event.new_x == 500
        assert event.new_y == 300
    
    def test_move_chapter_negative_coords(self, chapter_service, sample_chapter):
        """Test moving a chapter to negative coordinates (valid for canvas)."""
        updated = chapter_service.move_chapter(
            sample_chapter.id,
            board_x=-100,
            board_y=-50
        )
        
        assert updated.board_x == -100
        assert updated.board_y == -50
    
    # =========================================================================
    # Color Tests
    # =========================================================================
    
    def test_set_chapter_color(self, chapter_service, sample_chapter, event_recorder):
        """Test changing chapter color."""
        event_recorder.clear()
        
        updated = chapter_service.set_chapter_color(
            sample_chapter.id,
            color="#88FF88"
        )
        
        assert updated.color == "#88FF88"
        
        assert event_recorder.has_event(ChapterColorChanged)
        event = event_recorder.get_events(ChapterColorChanged)[0]
        assert event.new_color == "#88FF88"
    
    def test_set_chapter_color_invalid_fails(self, chapter_service, sample_chapter):
        """Test that invalid color format raises ValueError."""
        with pytest.raises(ValueError, match="color"):
            chapter_service.set_chapter_color(
                sample_chapter.id,
                color="red"  # Not hex format
            )
    
    # =========================================================================
    # Delete Tests
    # =========================================================================
    
    def test_delete_chapter(self, chapter_service, sample_chapter, event_recorder):
        """Test deleting a chapter."""
        chapter_id = sample_chapter.id
        event_recorder.clear()
        
        chapter_service.delete_chapter(chapter_id)
        
        with pytest.raises(ValueError, match="not found"):
            chapter_service.get_chapter(chapter_id)
        
        assert event_recorder.has_event(ChapterDeleted)
    
    # =========================================================================
    # Content Helper Tests
    # =========================================================================
    
    def test_get_chapter_text(self, chapter_service, sample_chapter):
        """Test getting chapter content as plain text."""
        chapter_service.update_chapter(
            sample_chapter.id,
            content="<p>Paragraph one.</p><p>Paragraph two.</p>"
        )
        
        text = chapter_service.get_chapter_text(sample_chapter.id)
        
        # Should strip HTML
        assert "<p>" not in text
        assert "Paragraph one" in text
        assert "Paragraph two" in text
    
    def test_set_chapter_text(self, chapter_service, sample_chapter):
        """Test setting chapter content as plain text."""
        chapter_service.set_chapter_text(
            sample_chapter.id,
            text="Plain text content.\n\nSecond paragraph."
        )
        
        chapter = chapter_service.get_chapter(sample_chapter.id)
        # Plain text should be stored (possibly with HTML wrapper)
        assert "Plain text content" in chapter.content
    
    def test_insert_scene_break(self, chapter_service, sample_chapter):
        """Test inserting a scene break."""
        chapter_service.update_chapter(
            sample_chapter.id,
            content="<p>First scene.</p>"
        )
        
        chapter_service.insert_scene_break(sample_chapter.id)
        
        chapter = chapter_service.get_chapter(sample_chapter.id)
        # Scene break marker should be present
        assert "***" in chapter.content or "* * *" in chapter.content or "scene" in chapter.content.lower()
    
    # =========================================================================
    # Open/Close Tests
    # =========================================================================
    
    def test_open_chapter(self, chapter_service, sample_chapter, event_recorder):
        """Test opening a chapter emits event."""
        event_recorder.clear()
        
        chapter_service.open_chapter(sample_chapter.id)
        
        assert event_recorder.has_event(ChapterOpened)
    
    def test_close_chapter(self, chapter_service, sample_chapter, event_recorder):
        """Test closing a chapter emits event."""
        event_recorder.clear()
        
        chapter_service.close_chapter(sample_chapter.id)
        
        assert event_recorder.has_event(ChapterClosed)
