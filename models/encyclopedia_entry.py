"""
Encyclopedia entry model for BlueWriter.
Represents world-building entries (characters, places, items, etc.)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import sqlite3


# Default categories for organization
DEFAULT_CATEGORIES = [
    "Character",
    "Location", 
    "Item",
    "Faction",
    "Event",
    "Concept",
    "General"
]


@dataclass
class EncyclopediaEntry:
    """Represents a world-building encyclopedia entry."""
    id: Optional[int] = None
    project_id: int = 0
    category: str = "General"
    name: str = ""
    content: str = ""
    tags: str = ""  # Comma-separated tags
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, conn: sqlite3.Connection, project_id: int, 
               name: str, category: str = "General", 
               content: str = "", tags: str = "") -> "EncyclopediaEntry":
        """Insert new entry and return instance."""
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO encyclopedia_entries 
               (project_id, category, name, content, tags) 
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, category, name, content, tags)
        )
        conn.commit()
        
        entry_id = cursor.lastrowid
        cursor.execute("SELECT * FROM encyclopedia_entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        
        return cls._from_row(row)
    
    @classmethod
    def get_by_id(cls, conn: sqlite3.Connection, entry_id: int) -> Optional["EncyclopediaEntry"]:
        """Get entry by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM encyclopedia_entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        return cls._from_row(row) if row else None
    
    @classmethod
    def get_by_project(cls, conn: sqlite3.Connection, project_id: int) -> List["EncyclopediaEntry"]:
        """Get all entries for a project, ordered by category then name."""
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM encyclopedia_entries 
               WHERE project_id = ? 
               ORDER BY category, name""",
            (project_id,)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_by_category(cls, conn: sqlite3.Connection, project_id: int, 
                        category: str) -> List["EncyclopediaEntry"]:
        """Get entries by category."""
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM encyclopedia_entries 
               WHERE project_id = ? AND category = ?
               ORDER BY name""",
            (project_id, category)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]
    
    @classmethod
    def search(cls, conn: sqlite3.Connection, project_id: int, 
               query: str) -> List["EncyclopediaEntry"]:
        """Search entries by name or content."""
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute(
            """SELECT * FROM encyclopedia_entries 
               WHERE project_id = ? AND (name LIKE ? OR content LIKE ? OR tags LIKE ?)
               ORDER BY category, name""",
            (project_id, search_term, search_term, search_term)
        )
        return [cls._from_row(row) for row in cursor.fetchall()]
    
    def update(self, conn: sqlite3.Connection) -> None:
        """Update entry in database."""
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE encyclopedia_entries 
               SET category = ?, name = ?, content = ?, tags = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (self.category, self.name, self.content, self.tags, self.id)
        )
        conn.commit()
    
    def delete(self, conn: sqlite3.Connection) -> None:
        """Delete entry from database."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM encyclopedia_entries WHERE id = ?", (self.id,))
        conn.commit()
    
    @classmethod
    def _from_row(cls, row: tuple) -> "EncyclopediaEntry":
        """Create instance from database row."""
        return cls(
            id=row[0],
            project_id=row[1],
            category=row[2],
            name=row[3],
            content=row[4],
            tags=row[5] or "",
            created_at=datetime.fromisoformat(row[6]) if row[6] else None,
            updated_at=datetime.fromisoformat(row[7]) if row[7] else None
        )
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]
    
    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from a list."""
        self.tags = ", ".join(tags)
