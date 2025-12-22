"""
Chapter service for BlueWriter.

Handles all chapter-related business logic and database operations.
Chapters are represented as sticky notes on the timeline canvas.
Emits events for state changes that UI can subscribe to.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from services.base import BaseService
from events.event_bus import EventBus
from events.events import (
    ChapterCreated,
    ChapterUpdated,
    ChapterDeleted,
    ChapterMoved,
    ChapterColorChanged,
    ChapterOpened,
    ChapterClosed,
)
from models.chapter import Chapter
from models.story import Story


# Color validation regex
COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')


@dataclass
class ChapterDTO:
    """Data transfer object for chapters.
    
    Used to pass chapter data between layers without
    exposing the database model directly.
    """
    id: int
    story_id: int
    title: str
    summary: str
    content: str
    board_x: float
    board_y: float
    color: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ChapterService(BaseService):
    """Service for managing chapters within stories.
    
    Provides CRUD operations, canvas positioning, color management,
    and content manipulation. Emits events for all state changes.
    
    Business Rules:
    - Cannot modify chapters in final_published stories
    - Color must be valid hex format (#RRGGBB)
    - Canvas positions can be any float values
    
    Example:
        event_bus = EventBus()
        service = ChapterService("/path/to/db", event_bus)
        
        # Create a chapter
        chapter = service.create_chapter(
            story_id=1, 
            title="Chapter One",
            board_x=100,
            board_y=200
        )
        
        # Move it on canvas
        service.move_chapter(chapter.id, board_x=300, board_y=400)
    """
    
    def __init__(self, db_path: str, event_bus: EventBus) -> None:
        """Initialize the chapter service.
        
        Args:
            db_path: Path to the SQLite database
            event_bus: EventBus for publishing events
        """
        super().__init__(db_path, event_bus)
    
    def _chapter_to_dto(self, chapter: Chapter) -> ChapterDTO:
        """Convert a Chapter model to ChapterDTO.
        
        Args:
            chapter: Chapter model instance
            
        Returns:
            ChapterDTO with the chapter data
        """
        return ChapterDTO(
            id=chapter.id,
            story_id=chapter.story_id,
            title=chapter.title,
            summary=chapter.summary,
            content=chapter.content,
            board_x=chapter.board_x,
            board_y=chapter.board_y,
            color=chapter.color,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
        )
    
    def _check_story_not_locked(self, conn, story_id: int) -> None:
        """Check that the parent story is not locked.
        
        Args:
            conn: Database connection
            story_id: The story's database ID
            
        Raises:
            RuntimeError: If story is final published (locked)
        """
        story = Story.get_by_id(conn, story_id)
        if story is None:
            raise ValueError(f"Story {story_id} not found")
        if story.is_locked:
            raise RuntimeError(
                f"Cannot modify chapter: story {story_id} is final published. "
                "Unpublish the story first to make changes."
            )
    
    def _validate_color(self, color: str) -> str:
        """Validate and normalize color format.
        
        Args:
            color: Color string to validate
            
        Returns:
            Uppercase color string
            
        Raises:
            ValueError: If color format is invalid
        """
        if not COLOR_PATTERN.match(color):
            raise ValueError(
                f"Invalid color format: {color}. "
                "Expected hex format #RRGGBB (e.g., #FFFF88)"
            )
        return color.upper()
    
    def list_chapters(self, story_id: int) -> List[ChapterDTO]:
        """Get all chapters for a story.
        
        Args:
            story_id: The story's database ID
            
        Returns:
            List of ChapterDTO objects, ordered by sort_order
        """
        conn = self._get_connection()
        try:
            chapters = Chapter.get_by_story(conn, story_id)
            return [self._chapter_to_dto(c) for c in chapters]
        finally:
            conn.close()
    
    def get_chapter(self, chapter_id: int) -> ChapterDTO:
        """Get a chapter by ID.
        
        Args:
            chapter_id: The chapter's database ID
            
        Returns:
            ChapterDTO with the chapter data
            
        Raises:
            ValueError: If chapter not found
        """
        conn = self._get_connection()
        try:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter is None:
                raise ValueError(f"Chapter {chapter_id} not found")
            return self._chapter_to_dto(chapter)
        finally:
            conn.close()
    
    def create_chapter(
        self,
        story_id: int,
        title: str,
        board_x: float = 100.0,
        board_y: float = 100.0,
        color: str = "#FFFF88",
    ) -> ChapterDTO:
        """Create a new chapter in a story.
        
        Args:
            story_id: The story's database ID
            title: Chapter title (required)
            board_x: X position on canvas (default 100)
            board_y: Y position on canvas (default 100)
            color: Sticky note color as hex (default yellow #FFFF88)
            
        Returns:
            ChapterDTO with the created chapter data
            
        Raises:
            ValueError: If title is empty or color format invalid
            RuntimeError: If story is locked
        """
        if not title or not title.strip():
            raise ValueError("Chapter title cannot be empty")
        
        color = self._validate_color(color)
        
        conn = self._get_connection()
        try:
            self._check_story_not_locked(conn, story_id)
            
            chapter = Chapter.create(conn, story_id, title.strip())
            chapter.board_x = board_x
            chapter.board_y = board_y
            chapter.color = color
            chapter.update(conn)
            
            dto = self._chapter_to_dto(chapter)
            
            # Emit event
            self.event_bus.publish(ChapterCreated(
                chapter_id=dto.id,
                story_id=dto.story_id,
                title=dto.title,
                board_x=dto.board_x,
                board_y=dto.board_y,
                color=dto.color,
            ))
            
            return dto
        finally:
            conn.close()
    
    def update_chapter(
        self,
        chapter_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        content: Optional[str] = None,
    ) -> ChapterDTO:
        """Update an existing chapter's metadata/content.
        
        Only provided fields will be updated.
        For position changes, use move_chapter().
        For color changes, use set_chapter_color().
        
        Args:
            chapter_id: The chapter's database ID
            title: New title (optional)
            summary: New summary (optional)
            content: New content as HTML (optional)
            
        Returns:
            ChapterDTO with the updated chapter data
            
        Raises:
            ValueError: If chapter not found or title is empty
            RuntimeError: If parent story is locked
        """
        conn = self._get_connection()
        try:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter is None:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            self._check_story_not_locked(conn, chapter.story_id)
            
            fields_changed = []
            
            if title is not None:
                if not title.strip():
                    raise ValueError("Chapter title cannot be empty")
                chapter.title = title.strip()
                fields_changed.append("title")
            
            if summary is not None:
                chapter.summary = summary
                fields_changed.append("summary")
            
            if content is not None:
                chapter.content = content
                fields_changed.append("content")
            
            if fields_changed:
                chapter.update(conn)
                
                # Emit event
                self.event_bus.publish(ChapterUpdated(
                    chapter_id=chapter_id,
                    fields_changed=fields_changed,
                ))
            
            # Re-fetch to get updated timestamp
            chapter = Chapter.get_by_id(conn, chapter_id)
            return self._chapter_to_dto(chapter)
        finally:
            conn.close()
    
    def delete_chapter(self, chapter_id: int) -> None:
        """Delete a chapter.
        
        Args:
            chapter_id: The chapter's database ID
            
        Raises:
            ValueError: If chapter not found
            RuntimeError: If parent story is locked
        """
        conn = self._get_connection()
        try:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter is None:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            self._check_story_not_locked(conn, chapter.story_id)
            
            story_id = chapter.story_id
            chapter.delete(conn)
            
            # Emit event
            self.event_bus.publish(ChapterDeleted(
                chapter_id=chapter_id,
                story_id=story_id,
            ))
        finally:
            conn.close()
    
    def move_chapter(
        self,
        chapter_id: int,
        board_x: float,
        board_y: float,
    ) -> ChapterDTO:
        """Move a chapter's sticky note on the canvas.
        
        Args:
            chapter_id: The chapter's database ID
            board_x: New X position
            board_y: New Y position
            
        Returns:
            ChapterDTO with the updated chapter data
            
        Raises:
            ValueError: If chapter not found
            RuntimeError: If parent story is locked
        """
        conn = self._get_connection()
        try:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter is None:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            self._check_story_not_locked(conn, chapter.story_id)
            
            old_x, old_y = chapter.board_x, chapter.board_y
            chapter.board_x = board_x
            chapter.board_y = board_y
            chapter.update(conn)
            
            # Emit event
            self.event_bus.publish(ChapterMoved(
                chapter_id=chapter_id,
                old_x=old_x,
                old_y=old_y,
                new_x=board_x,
                new_y=board_y,
            ))
            
            # Re-fetch to get updated timestamp
            chapter = Chapter.get_by_id(conn, chapter_id)
            return self._chapter_to_dto(chapter)
        finally:
            conn.close()
    
    def set_chapter_color(self, chapter_id: int, color: str) -> ChapterDTO:
        """Change a chapter's sticky note color.
        
        Args:
            chapter_id: The chapter's database ID
            color: New color as hex (#RRGGBB)
            
        Returns:
            ChapterDTO with the updated chapter data
            
        Raises:
            ValueError: If chapter not found or color format invalid
            RuntimeError: If parent story is locked
        """
        color = self._validate_color(color)
        
        conn = self._get_connection()
        try:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter is None:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            self._check_story_not_locked(conn, chapter.story_id)
            
            old_color = chapter.color
            chapter.color = color
            chapter.update(conn)
            
            # Emit event
            self.event_bus.publish(ChapterColorChanged(
                chapter_id=chapter_id,
                old_color=old_color,
                new_color=color,
            ))
            
            # Re-fetch to get updated timestamp
            chapter = Chapter.get_by_id(conn, chapter_id)
            return self._chapter_to_dto(chapter)
        finally:
            conn.close()

    # =========================================================================
    # Content Helper Methods
    # =========================================================================
    
    def get_chapter_text(self, chapter_id: int) -> str:
        """Get chapter content as plain text.
        
        Strips HTML tags and returns plain text content.
        Useful for word counts, searches, and AI processing.
        
        Args:
            chapter_id: The chapter's database ID
            
        Returns:
            Plain text content
            
        Raises:
            ValueError: If chapter not found
        """
        dto = self.get_chapter(chapter_id)
        # Simple HTML tag removal - could be enhanced with proper HTML parsing
        text = re.sub(r'<[^>]+>', '', dto.content)
        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        return text.strip()
    
    def set_chapter_text(self, chapter_id: int, text: str) -> ChapterDTO:
        """Set chapter content as plain text.
        
        Converts plain text to simple HTML paragraphs.
        Useful for importing plain text content.
        
        Args:
            chapter_id: The chapter's database ID
            text: Plain text content to set
            
        Returns:
            ChapterDTO with the updated chapter data
            
        Raises:
            ValueError: If chapter not found
            RuntimeError: If parent story is locked
        """
        # Convert plain text to HTML paragraphs
        paragraphs = text.split('\n\n')
        html_parts = []
        for p in paragraphs:
            p = p.strip()
            if p:
                # Escape HTML entities and wrap in paragraph
                p = p.replace('&', '&amp;')
                p = p.replace('<', '&lt;')
                p = p.replace('>', '&gt;')
                p = p.replace('\n', '<br/>')
                html_parts.append(f'<p>{p}</p>')
        
        html_content = '\n'.join(html_parts)
        return self.update_chapter(chapter_id, content=html_content)
    
    def get_chapter_html(self, chapter_id: int) -> str:
        """Get chapter content as raw HTML.
        
        Returns the stored HTML content without modification.
        
        Args:
            chapter_id: The chapter's database ID
            
        Returns:
            HTML content string
            
        Raises:
            ValueError: If chapter not found
        """
        dto = self.get_chapter(chapter_id)
        return dto.content
    
    def set_chapter_html(self, chapter_id: int, html: str) -> ChapterDTO:
        """Set chapter content as HTML.
        
        Stores the HTML content directly.
        
        Args:
            chapter_id: The chapter's database ID
            html: HTML content to set
            
        Returns:
            ChapterDTO with the updated chapter data
            
        Raises:
            ValueError: If chapter not found
            RuntimeError: If parent story is locked
        """
        return self.update_chapter(chapter_id, content=html)
    
    def insert_text(self, chapter_id: int, position: int, text: str) -> ChapterDTO:
        """Insert text at a specific position in the chapter.
        
        Note: Position is character-based in the HTML content.
        For rich text editing, the UI should handle cursor positioning.
        
        Args:
            chapter_id: The chapter's database ID
            position: Character position to insert at
            text: Text to insert
            
        Returns:
            ChapterDTO with the updated chapter data
            
        Raises:
            ValueError: If chapter not found or position invalid
            RuntimeError: If parent story is locked
        """
        dto = self.get_chapter(chapter_id)
        content = dto.content
        
        if position < 0:
            position = 0
        if position > len(content):
            position = len(content)
        
        # Escape text for HTML
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        new_content = content[:position] + text + content[position:]
        return self.update_chapter(chapter_id, content=new_content)
    
    def insert_scene_break(self, chapter_id: int, position: int = -1) -> ChapterDTO:
        """Insert a scene break (***) at the specified position.
        
        If position is -1, appends to the end of the content.
        
        Args:
            chapter_id: The chapter's database ID
            position: Character position to insert at (-1 for end)
            
        Returns:
            ChapterDTO with the updated chapter data
            
        Raises:
            ValueError: If chapter not found
            RuntimeError: If parent story is locked
        """
        scene_break_html = '<p style="text-align: center;">* * *</p>'
        
        dto = self.get_chapter(chapter_id)
        content = dto.content
        
        if position == -1:
            new_content = content + '\n' + scene_break_html
        else:
            if position < 0:
                position = 0
            if position > len(content):
                position = len(content)
            new_content = content[:position] + scene_break_html + content[position:]
        
        return self.update_chapter(chapter_id, content=new_content)
    
    # =========================================================================
    # Editor State Methods
    # =========================================================================
    
    def open_chapter(self, chapter_id: int) -> ChapterDTO:
        """Open a chapter in the editor.
        
        Emits a ChapterOpened event that the UI can respond to.
        
        Args:
            chapter_id: The chapter's database ID
            
        Returns:
            ChapterDTO with the chapter data
            
        Raises:
            ValueError: If chapter not found
        """
        dto = self.get_chapter(chapter_id)  # Validates existence
        
        # Emit event
        self.event_bus.publish(ChapterOpened(
            chapter_id=chapter_id,
        ))
        
        return dto
    
    def close_chapter(self, chapter_id: int) -> None:
        """Close a chapter editor.
        
        Emits a ChapterClosed event that the UI can respond to.
        
        Args:
            chapter_id: The chapter's database ID
            
        Raises:
            ValueError: If chapter not found
        """
        # Validate chapter exists
        self.get_chapter(chapter_id)
        
        # Emit event
        self.event_bus.publish(ChapterClosed(
            chapter_id=chapter_id,
        ))
