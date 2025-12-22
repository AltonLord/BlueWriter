"""
Story service for BlueWriter.

Handles all story-related business logic and database operations.
Emits events for state changes that UI can subscribe to.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from services.base import BaseService
from events.event_bus import EventBus
from events.events import (
    StoryCreated,
    StoryUpdated,
    StoryDeleted,
    StorySelected,
    StoryPublished,
    StoryUnpublished,
    StoriesReordered,
)
from models.story import Story, STATUS_DRAFT, STATUS_ROUGH_PUBLISHED, STATUS_FINAL_PUBLISHED


@dataclass
class StoryDTO:
    """Data transfer object for stories.
    
    Used to pass story data between layers without
    exposing the database model directly.
    """
    id: int
    project_id: int
    title: str
    synopsis: str
    sort_order: int
    status: str
    published_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    @property
    def is_locked(self) -> bool:
        """Check if story is locked (final published)."""
        return self.status == STATUS_FINAL_PUBLISHED
    
    @property
    def is_published(self) -> bool:
        """Check if story has been published (rough or final)."""
        return self.status in (STATUS_ROUGH_PUBLISHED, STATUS_FINAL_PUBLISHED)


class StoryService(BaseService):
    """Service for managing stories within projects.
    
    Provides CRUD operations for stories, publishing/unpublishing,
    and reordering. Emits events for all state changes.
    
    Business Rules:
    - Cannot update or delete final_published stories without unpublishing first
    - Stories have a sort_order within their project
    - Publishing sets the published_at timestamp
    
    Example:
        event_bus = EventBus()
        service = StoryService("/path/to/db", event_bus)
        
        # Create a story
        story = service.create_story(project_id=1, title="Book One")
        
        # Publish it
        service.publish_story(story.id, final=False)
    """
    
    def __init__(self, db_path: str, event_bus: EventBus) -> None:
        """Initialize the story service.
        
        Args:
            db_path: Path to the SQLite database
            event_bus: EventBus for publishing events
        """
        super().__init__(db_path, event_bus)
    
    def _story_to_dto(self, story: Story) -> StoryDTO:
        """Convert a Story model to StoryDTO.
        
        Args:
            story: Story model instance
            
        Returns:
            StoryDTO with the story data
        """
        return StoryDTO(
            id=story.id,
            project_id=story.project_id,
            title=story.title,
            synopsis=story.synopsis,
            sort_order=story.sort_order,
            status=story.status,
            published_at=story.published_at,
            created_at=story.created_at,
            updated_at=story.updated_at,
        )
    
    def list_stories(self, project_id: int) -> List[StoryDTO]:
        """Get all stories for a project.
        
        Args:
            project_id: The project's database ID
            
        Returns:
            List of StoryDTO objects, ordered by sort_order
        """
        conn = self._get_connection()
        try:
            stories = Story.get_by_project(conn, project_id)
            return [self._story_to_dto(s) for s in stories]
        finally:
            conn.close()
    
    def get_story(self, story_id: int) -> StoryDTO:
        """Get a story by ID.
        
        Args:
            story_id: The story's database ID
            
        Returns:
            StoryDTO with the story data
            
        Raises:
            ValueError: If story not found
        """
        conn = self._get_connection()
        try:
            story = Story.get_by_id(conn, story_id)
            if story is None:
                raise ValueError(f"Story {story_id} not found")
            return self._story_to_dto(story)
        finally:
            conn.close()
    
    def create_story(
        self,
        project_id: int,
        title: str,
        synopsis: str = "",
    ) -> StoryDTO:
        """Create a new story in a project.
        
        Args:
            project_id: The project's database ID
            title: Story title (required)
            synopsis: Optional story synopsis
            
        Returns:
            StoryDTO with the created story data
            
        Raises:
            ValueError: If title is empty
        """
        if not title or not title.strip():
            raise ValueError("Story title cannot be empty")
        
        conn = self._get_connection()
        try:
            story = Story.create(conn, project_id, title.strip(), synopsis)
            dto = self._story_to_dto(story)
            
            # Emit event
            self.event_bus.publish(StoryCreated(
                story_id=dto.id,
                project_id=dto.project_id,
                title=dto.title,
            ))
            
            return dto
        finally:
            conn.close()
    
    def update_story(
        self,
        story_id: int,
        title: Optional[str] = None,
        synopsis: Optional[str] = None,
    ) -> StoryDTO:
        """Update an existing story.
        
        Only provided fields will be updated.
        Cannot update final_published stories.
        
        Args:
            story_id: The story's database ID
            title: New title (optional)
            synopsis: New synopsis (optional)
            
        Returns:
            StoryDTO with the updated story data
            
        Raises:
            ValueError: If story not found or title is empty
            RuntimeError: If story is locked (final published)
        """
        conn = self._get_connection()
        try:
            story = Story.get_by_id(conn, story_id)
            if story is None:
                raise ValueError(f"Story {story_id} not found")
            
            if story.is_locked:
                raise RuntimeError(
                    f"Cannot modify story {story_id}: final published. "
                    "Unpublish first to make changes."
                )
            
            fields_changed = []
            
            if title is not None:
                if not title.strip():
                    raise ValueError("Story title cannot be empty")
                story.title = title.strip()
                fields_changed.append("title")
            
            if synopsis is not None:
                story.synopsis = synopsis
                fields_changed.append("synopsis")
            
            if fields_changed:
                story.update(conn)
                
                # Emit event
                self.event_bus.publish(StoryUpdated(
                    story_id=story_id,
                    fields_changed=fields_changed,
                ))
            
            # Re-fetch to get updated timestamp
            story = Story.get_by_id(conn, story_id)
            return self._story_to_dto(story)
        finally:
            conn.close()
    
    def delete_story(self, story_id: int) -> None:
        """Delete a story.
        
        This will also delete all chapters in the story
        due to foreign key cascades.
        Cannot delete final_published stories.
        
        Args:
            story_id: The story's database ID
            
        Raises:
            ValueError: If story not found
            RuntimeError: If story is locked (final published)
        """
        conn = self._get_connection()
        try:
            story = Story.get_by_id(conn, story_id)
            if story is None:
                raise ValueError(f"Story {story_id} not found")
            
            if story.is_locked:
                raise RuntimeError(
                    f"Cannot delete story {story_id}: final published. "
                    "Unpublish first to delete."
                )
            
            story.delete(conn)
            
            # Emit event
            self.event_bus.publish(StoryDeleted(
                story_id=story_id,
            ))
        finally:
            conn.close()
    
    def select_story(self, story_id: int) -> StoryDTO:
        """Select a story in the UI.
        
        Emits a StorySelected event that the UI can
        respond to by loading the story's chapters.
        
        Args:
            story_id: The story's database ID
            
        Returns:
            StoryDTO with the story data
            
        Raises:
            ValueError: If story not found
        """
        dto = self.get_story(story_id)  # Validates existence
        
        # Emit event
        self.event_bus.publish(StorySelected(
            story_id=story_id,
        ))
        
        return dto
    
    def publish_story(self, story_id: int, final: bool = False) -> StoryDTO:
        """Publish a story.
        
        Args:
            story_id: The story's database ID
            final: If True, mark as final_published (locks the story).
                   If False, mark as rough_published.
                   
        Returns:
            StoryDTO with the updated story data
            
        Raises:
            ValueError: If story not found
        """
        conn = self._get_connection()
        try:
            story = Story.get_by_id(conn, story_id)
            if story is None:
                raise ValueError(f"Story {story_id} not found")
            
            if final:
                story.publish_final(conn)
                status = STATUS_FINAL_PUBLISHED
            else:
                story.publish_rough(conn)
                status = STATUS_ROUGH_PUBLISHED
            
            # Emit event
            self.event_bus.publish(StoryPublished(
                story_id=story_id,
                status=status,
            ))
            
            # Re-fetch to get updated data
            story = Story.get_by_id(conn, story_id)
            return self._story_to_dto(story)
        finally:
            conn.close()
    
    def unpublish_story(self, story_id: int) -> StoryDTO:
        """Unpublish a story (revert to draft).
        
        This unlocks final_published stories, allowing
        them to be edited or deleted again.
        
        Args:
            story_id: The story's database ID
            
        Returns:
            StoryDTO with the updated story data
            
        Raises:
            ValueError: If story not found
        """
        conn = self._get_connection()
        try:
            story = Story.get_by_id(conn, story_id)
            if story is None:
                raise ValueError(f"Story {story_id} not found")
            
            story.unpublish(conn)
            
            # Emit event
            self.event_bus.publish(StoryUnpublished(
                story_id=story_id,
            ))
            
            # Re-fetch to get updated data
            story = Story.get_by_id(conn, story_id)
            return self._story_to_dto(story)
        finally:
            conn.close()
    
    def reorder_stories(self, project_id: int, story_ids: List[int]) -> None:
        """Reorder stories within a project.
        
        Updates the sort_order of each story to match the
        position in the provided list.
        
        Args:
            project_id: The project's database ID
            story_ids: List of story IDs in the desired order
            
        Raises:
            ValueError: If any story_id doesn't belong to the project
            RuntimeError: If any story is locked (final published)
        """
        conn = self._get_connection()
        try:
            # Validate all stories exist and belong to project
            existing_stories = Story.get_by_project(conn, project_id)
            existing_ids = {s.id for s in existing_stories}
            
            for sid in story_ids:
                if sid not in existing_ids:
                    raise ValueError(
                        f"Story {sid} not found in project {project_id}"
                    )
            
            # Check for locked stories
            for story in existing_stories:
                if story.id in story_ids and story.is_locked:
                    raise RuntimeError(
                        f"Cannot reorder: story {story.id} is final published"
                    )
            
            # Update sort_order for each story
            cursor = conn.cursor()
            for new_order, sid in enumerate(story_ids):
                cursor.execute(
                    "UPDATE stories SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_order, sid)
                )
            conn.commit()
            
            # Emit event
            self.event_bus.publish(StoriesReordered(
                project_id=project_id,
                story_ids=story_ids,
            ))
        finally:
            conn.close()
