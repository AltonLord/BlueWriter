"""
Encyclopedia service for BlueWriter.

Handles all encyclopedia entry operations for world-building.
Entries are organized by category and can be searched.
Emits events for state changes that UI can subscribe to.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from services.base import BaseService
from events.event_bus import EventBus
from events.events import (
    EntryCreated,
    EntryUpdated,
    EntryDeleted,
    EntryOpened,
    EntryClosed,
)
from models.encyclopedia_entry import EncyclopediaEntry, DEFAULT_CATEGORIES


@dataclass
class EncyclopediaEntryDTO:
    """Data transfer object for encyclopedia entries.
    
    Used to pass entry data between layers without
    exposing the database model directly.
    """
    id: int
    project_id: int
    name: str
    category: str
    content: str
    tags: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class EncyclopediaService(BaseService):
    """Service for managing encyclopedia entries.
    
    Provides CRUD operations, category filtering, and search.
    Emits events for all state changes.
    
    Example:
        event_bus = EventBus()
        service = EncyclopediaService("/path/to/db", event_bus)
        
        # Create an entry
        entry = service.create_entry(
            project_id=1,
            name="John Smith",
            category="Character",
            content="The protagonist...",
            tags="protagonist, hero"
        )
        
        # Search entries
        results = service.search_entries(project_id=1, query="hero")
    """
    
    def __init__(self, db_path: str, event_bus: EventBus) -> None:
        """Initialize the encyclopedia service.
        
        Args:
            db_path: Path to the SQLite database
            event_bus: EventBus for publishing events
        """
        super().__init__(db_path, event_bus)
    
    def _entry_to_dto(self, entry: EncyclopediaEntry) -> EncyclopediaEntryDTO:
        """Convert an EncyclopediaEntry model to DTO.
        
        Args:
            entry: EncyclopediaEntry model instance
            
        Returns:
            EncyclopediaEntryDTO with the entry data
        """
        return EncyclopediaEntryDTO(
            id=entry.id,
            project_id=entry.project_id,
            name=entry.name,
            category=entry.category,
            content=entry.content,
            tags=entry.tags,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
    
    def list_entries(
        self,
        project_id: int,
        category: Optional[str] = None,
    ) -> List[EncyclopediaEntryDTO]:
        """Get all encyclopedia entries for a project.
        
        Args:
            project_id: The project's database ID
            category: Optional category filter
            
        Returns:
            List of EncyclopediaEntryDTO objects, ordered by category then name
        """
        conn = self._get_connection()
        try:
            if category:
                entries = EncyclopediaEntry.get_by_category(conn, project_id, category)
            else:
                entries = EncyclopediaEntry.get_by_project(conn, project_id)
            return [self._entry_to_dto(e) for e in entries]
        finally:
            conn.close()
    
    def get_entry(self, entry_id: int) -> EncyclopediaEntryDTO:
        """Get an encyclopedia entry by ID.
        
        Args:
            entry_id: The entry's database ID
            
        Returns:
            EncyclopediaEntryDTO with the entry data
            
        Raises:
            ValueError: If entry not found
        """
        conn = self._get_connection()
        try:
            entry = EncyclopediaEntry.get_by_id(conn, entry_id)
            if entry is None:
                raise ValueError(f"Encyclopedia entry {entry_id} not found")
            return self._entry_to_dto(entry)
        finally:
            conn.close()
    
    def create_entry(
        self,
        project_id: int,
        name: str,
        category: str,
        content: str = "",
        tags: str = "",
    ) -> EncyclopediaEntryDTO:
        """Create a new encyclopedia entry.
        
        Args:
            project_id: The project's database ID
            name: Entry name (required)
            category: Entry category (e.g., "Character", "Location")
            content: Entry content/description
            tags: Comma-separated tags
            
        Returns:
            EncyclopediaEntryDTO with the created entry data
            
        Raises:
            ValueError: If name is empty
        """
        if not name or not name.strip():
            raise ValueError("Entry name cannot be empty")
        
        conn = self._get_connection()
        try:
            entry = EncyclopediaEntry.create(
                conn,
                project_id=project_id,
                name=name.strip(),
                category=category,
                content=content,
                tags=tags,
            )
            dto = self._entry_to_dto(entry)
            
            # Emit event
            self.event_bus.publish(EntryCreated(
                entry_id=dto.id,
                project_id=dto.project_id,
                name=dto.name,
                category=dto.category,
            ))
            
            return dto
        finally:
            conn.close()
    
    def update_entry(
        self,
        entry_id: int,
        name: Optional[str] = None,
        category: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> EncyclopediaEntryDTO:
        """Update an existing encyclopedia entry.
        
        Only provided fields will be updated.
        
        Args:
            entry_id: The entry's database ID
            name: New name (optional)
            category: New category (optional)
            content: New content (optional)
            tags: New tags (optional)
            
        Returns:
            EncyclopediaEntryDTO with the updated entry data
            
        Raises:
            ValueError: If entry not found or name is empty
        """
        conn = self._get_connection()
        try:
            entry = EncyclopediaEntry.get_by_id(conn, entry_id)
            if entry is None:
                raise ValueError(f"Encyclopedia entry {entry_id} not found")
            
            fields_changed = []
            
            if name is not None:
                if not name.strip():
                    raise ValueError("Entry name cannot be empty")
                entry.name = name.strip()
                fields_changed.append("name")
            
            if category is not None:
                entry.category = category
                fields_changed.append("category")
            
            if content is not None:
                entry.content = content
                fields_changed.append("content")
            
            if tags is not None:
                entry.tags = tags
                fields_changed.append("tags")
            
            if fields_changed:
                entry.update(conn)
                
                # Emit event
                self.event_bus.publish(EntryUpdated(
                    entry_id=entry_id,
                    fields_changed=fields_changed,
                ))
            
            # Re-fetch to get updated timestamp
            entry = EncyclopediaEntry.get_by_id(conn, entry_id)
            return self._entry_to_dto(entry)
        finally:
            conn.close()
    
    def delete_entry(self, entry_id: int) -> None:
        """Delete an encyclopedia entry.
        
        Args:
            entry_id: The entry's database ID
            
        Raises:
            ValueError: If entry not found
        """
        conn = self._get_connection()
        try:
            entry = EncyclopediaEntry.get_by_id(conn, entry_id)
            if entry is None:
                raise ValueError(f"Encyclopedia entry {entry_id} not found")
            
            project_id = entry.project_id
            entry.delete(conn)
            
            # Emit event
            self.event_bus.publish(EntryDeleted(
                entry_id=entry_id,
                project_id=project_id,
            ))
        finally:
            conn.close()
    
    def search_entries(
        self,
        project_id: int,
        query: str,
    ) -> List[EncyclopediaEntryDTO]:
        """Search encyclopedia entries by keyword.
        
        Searches name, content, and tags fields.
        
        Args:
            project_id: The project's database ID
            query: Search keyword
            
        Returns:
            List of matching EncyclopediaEntryDTO objects
        """
        if not query or not query.strip():
            return []
        
        conn = self._get_connection()
        try:
            entries = EncyclopediaEntry.search(conn, project_id, query.strip())
            return [self._entry_to_dto(e) for e in entries]
        finally:
            conn.close()
    
    def list_categories(self, project_id: int) -> List[str]:
        """List all categories in use for a project.
        
        Returns categories that have at least one entry,
        plus the default categories.
        
        Args:
            project_id: The project's database ID
            
        Returns:
            List of category names (sorted)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT DISTINCT category FROM encyclopedia_entries 
                   WHERE project_id = ? ORDER BY category""",
                (project_id,)
            )
            used_categories = {row[0] for row in cursor.fetchall()}
            
            # Combine with default categories
            all_categories = set(DEFAULT_CATEGORIES) | used_categories
            return sorted(all_categories)
        finally:
            conn.close()
    
    def get_default_categories(self) -> List[str]:
        """Get the list of default categories.
        
        Returns:
            List of default category names
        """
        return list(DEFAULT_CATEGORIES)
    
    # =========================================================================
    # Editor State Methods
    # =========================================================================
    
    def open_entry(self, entry_id: int) -> EncyclopediaEntryDTO:
        """Open an encyclopedia entry in the editor.
        
        Emits an EntryOpened event that the UI can respond to.
        
        Args:
            entry_id: The entry's database ID
            
        Returns:
            EncyclopediaEntryDTO with the entry data
            
        Raises:
            ValueError: If entry not found
        """
        dto = self.get_entry(entry_id)  # Validates existence
        
        # Emit event
        self.event_bus.publish(EntryOpened(
            entry_id=entry_id,
        ))
        
        return dto
    
    def close_entry(self, entry_id: int) -> None:
        """Close an encyclopedia entry editor.
        
        Emits an EntryClosed event that the UI can respond to.
        
        Args:
            entry_id: The entry's database ID
            
        Raises:
            ValueError: If entry not found
        """
        # Validate entry exists
        self.get_entry(entry_id)
        
        # Emit event
        self.event_bus.publish(EntryClosed(
            entry_id=entry_id,
        ))
