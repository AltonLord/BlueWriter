"""
Unit tests for StoryService.

Tests all CRUD operations, publishing, and event emission for stories.
"""
import pytest
from events.events import (
    StoryCreated, StoryUpdated, StoryDeleted, StorySelected,
    StoryPublished, StoryUnpublished, StoriesReordered
)


class TestStoryService:
    """Test cases for StoryService."""
    
    # =========================================================================
    # Create Tests
    # =========================================================================
    
    def test_create_story(self, story_service, sample_project, event_recorder):
        """Test creating a new story."""
        event_recorder.clear()
        
        story = story_service.create_story(
            project_id=sample_project.id,
            title="My Story",
            synopsis="An interesting tale"
        )
        
        assert story.id is not None
        assert story.project_id == sample_project.id
        assert story.title == "My Story"
        assert story.synopsis == "An interesting tale"
        assert story.status == "draft"
    
    def test_create_story_emits_event(self, story_service, sample_project, event_recorder):
        """Test that creating a story emits StoryCreated event."""
        event_recorder.clear()
        
        story = story_service.create_story(
            project_id=sample_project.id,
            title="Event Test"
        )
        
        assert event_recorder.has_event(StoryCreated)
        events = event_recorder.get_events(StoryCreated)
        assert len(events) == 1
        assert events[0].story_id == story.id
        assert events[0].project_id == sample_project.id
        assert events[0].title == "Event Test"
    
    def test_create_story_empty_title_fails(self, story_service, sample_project):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            story_service.create_story(project_id=sample_project.id, title="")
    
    def test_create_story_invalid_project_fails(self, story_service):
        """Test that invalid project ID raises an error."""
        import sqlite3
        with pytest.raises((ValueError, sqlite3.IntegrityError)):
            story_service.create_story(project_id=99999, title="Test")
    
    # =========================================================================
    # Read Tests
    # =========================================================================
    
    def test_list_stories_empty(self, story_service, sample_project):
        """Test listing stories when none exist."""
        stories = story_service.list_stories(sample_project.id)
        assert stories == []
    
    def test_list_stories(self, story_service, sample_project):
        """Test listing multiple stories."""
        story_service.create_story(project_id=sample_project.id, title="Story A")
        story_service.create_story(project_id=sample_project.id, title="Story B")
        story_service.create_story(project_id=sample_project.id, title="Story C")
        
        stories = story_service.list_stories(sample_project.id)
        
        assert len(stories) == 3
        titles = [s.title for s in stories]
        assert "Story A" in titles
        assert "Story B" in titles
        assert "Story C" in titles
    
    def test_get_story(self, story_service, sample_project):
        """Test getting a story by ID."""
        created = story_service.create_story(
            project_id=sample_project.id,
            title="Get Test",
            synopsis="Test synopsis"
        )
        
        fetched = story_service.get_story(created.id)
        
        assert fetched.id == created.id
        assert fetched.title == "Get Test"
        assert fetched.synopsis == "Test synopsis"
    
    def test_get_story_not_found(self, story_service):
        """Test getting a non-existent story raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            story_service.get_story(99999)
    
    # =========================================================================
    # Update Tests
    # =========================================================================
    
    def test_update_story_title(self, story_service, sample_story, event_recorder):
        """Test updating story title."""
        event_recorder.clear()
        
        updated = story_service.update_story(sample_story.id, title="New Title")
        
        assert updated.title == "New Title"
        assert event_recorder.has_event(StoryUpdated)
    
    def test_update_story_synopsis(self, story_service, sample_story):
        """Test updating story synopsis."""
        updated = story_service.update_story(
            sample_story.id,
            synopsis="New synopsis"
        )
        
        assert updated.synopsis == "New synopsis"
        assert updated.title == sample_story.title  # Unchanged
    
    def test_update_story_not_found(self, story_service):
        """Test updating a non-existent story raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            story_service.update_story(99999, title="New")
    
    # =========================================================================
    # Delete Tests
    # =========================================================================
    
    def test_delete_story(self, story_service, sample_story, event_recorder):
        """Test deleting a story."""
        story_id = sample_story.id
        event_recorder.clear()
        
        story_service.delete_story(story_id)
        
        with pytest.raises(ValueError, match="not found"):
            story_service.get_story(story_id)
        
        assert event_recorder.has_event(StoryDeleted)
    
    def test_delete_story_not_found(self, story_service):
        """Test deleting a non-existent story raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            story_service.delete_story(99999)
    
    # =========================================================================
    # Select Tests
    # =========================================================================
    
    def test_select_story(self, story_service, sample_story, event_recorder):
        """Test selecting a story emits StorySelected event."""
        event_recorder.clear()
        
        result = story_service.select_story(sample_story.id)
        
        assert result.id == sample_story.id
        assert event_recorder.has_event(StorySelected)
    
    # =========================================================================
    # Publishing Tests
    # =========================================================================
    
    def test_publish_story_rough(self, story_service, sample_story, event_recorder):
        """Test rough publishing a story."""
        event_recorder.clear()
        
        result = story_service.publish_story(sample_story.id, final=False)
        
        assert result.status == "rough_published"
        assert event_recorder.has_event(StoryPublished)
        event = event_recorder.get_events(StoryPublished)[0]
        assert event.status == "rough_published"
    
    def test_publish_story_final(self, story_service, sample_story, event_recorder):
        """Test final publishing a story."""
        event_recorder.clear()
        
        result = story_service.publish_story(sample_story.id, final=True)
        
        assert result.status == "final_published"
        assert event_recorder.has_event(StoryPublished)
        event = event_recorder.get_events(StoryPublished)[0]
        assert event.status == "final_published"
    
    def test_unpublish_story(self, story_service, sample_story, event_recorder):
        """Test unpublishing a story."""
        story_service.publish_story(sample_story.id, final=True)
        event_recorder.clear()
        
        result = story_service.unpublish_story(sample_story.id)
        
        assert result.status == "draft"
        assert event_recorder.has_event(StoryUnpublished)
    
    def test_cannot_update_final_published(self, story_service, sample_story):
        """Test that final published stories cannot be updated."""
        story_service.publish_story(sample_story.id, final=True)
        
        with pytest.raises(RuntimeError, match="final published"):
            story_service.update_story(sample_story.id, title="New Title")
    
    def test_cannot_delete_final_published(self, story_service, sample_story):
        """Test that final published stories cannot be deleted."""
        story_service.publish_story(sample_story.id, final=True)
        
        with pytest.raises(RuntimeError, match="final published"):
            story_service.delete_story(sample_story.id)
    
    # =========================================================================
    # Reorder Tests
    # =========================================================================
    
    def test_reorder_stories(self, story_service, sample_project, event_recorder):
        """Test reordering stories."""
        s1 = story_service.create_story(project_id=sample_project.id, title="First")
        s2 = story_service.create_story(project_id=sample_project.id, title="Second")
        s3 = story_service.create_story(project_id=sample_project.id, title="Third")
        event_recorder.clear()
        
        # Reorder: Third, First, Second
        story_service.reorder_stories(sample_project.id, [s3.id, s1.id, s2.id])
        
        stories = story_service.list_stories(sample_project.id)
        assert stories[0].id == s3.id
        assert stories[1].id == s1.id
        assert stories[2].id == s2.id
        
        assert event_recorder.has_event(StoriesReordered)
