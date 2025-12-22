"""
Story model for BlueWriter.
Represents an individual book within a project.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import sqlite3


# Publication status constants
STATUS_DRAFT = "draft"
STATUS_ROUGH_PUBLISHED = "rough_published"
STATUS_FINAL_PUBLISHED = "final_published"

# Explicit column list for consistent ordering
STORY_COLUMNS = "id, project_id, title, synopsis, sort_order, status, published_at, created_at, updated_at"


@dataclass
class Story:
    """Represents an individual book within a project."""
    id: Optional[int] = None
    project_id: int = 0
    title: str = ""
    synopsis: str = ""
    sort_order: int = 0
    status: str = STATUS_DRAFT
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_locked(self) -> bool:
        """Check if story is locked (final published)."""
        return self.status == STATUS_FINAL_PUBLISHED
    
    @property
    def is_published(self) -> bool:
        """Check if story has been published (rough or final)."""
        return self.status in (STATUS_ROUGH_PUBLISHED, STATUS_FINAL_PUBLISHED)
    
    @classmethod
    def _from_row(cls, row) -> "Story":
        """Create Story from database row (expects columns in STORY_COLUMNS order)."""
        return cls(
            id=row[0],
            project_id=row[1],
            title=row[2],
            synopsis=row[3],
            sort_order=row[4],
            status=row[5] if row[5] else STATUS_DRAFT,
            published_at=datetime.fromisoformat(row[6]) if row[6] else None,
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None
        )
    
    @classmethod
    def create(cls, conn: sqlite3.Connection, project_id: int, title: str, synopsis: str = "") -> "Story":
        """Insert new story and return instance."""
        cursor = conn.cursor()
        
        # Get next sort_order value for this project
        cursor.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM stories WHERE project_id = ?",
            (project_id,)
        )
        next_sort_order = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO stories (project_id, title, synopsis, sort_order, status) VALUES (?, ?, ?, ?, ?)",
            (project_id, title, synopsis, next_sort_order, STATUS_DRAFT)
        )
        conn.commit()
        
        # Get the inserted story
        story_id = cursor.lastrowid
        return cls.get_by_id(conn, story_id)
    
    @classmethod
    def get_by_id(cls, conn: sqlite3.Connection, story_id: int) -> Optional["Story"]:
        """Retrieve story by ID."""
        cursor = conn.cursor()
        cursor.execute(f"SELECT {STORY_COLUMNS} FROM stories WHERE id = ?", (story_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        return cls._from_row(row)
    
    @classmethod
    def get_by_project(cls, conn: sqlite3.Connection, project_id: int) -> List["Story"]:
        """Retrieve all stories for a project, in order."""
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {STORY_COLUMNS} FROM stories WHERE project_id = ? ORDER BY sort_order ASC, created_at ASC",
            (project_id,)
        )
        rows = cursor.fetchall()
        return [cls._from_row(row) for row in rows]
    
    @classmethod
    def get_all(cls, conn: sqlite3.Connection) -> List["Story"]:
        """Retrieve all stories."""
        cursor = conn.cursor()
        cursor.execute(f"SELECT {STORY_COLUMNS} FROM stories ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [cls._from_row(row) for row in rows]
    
    def update(self, conn: sqlite3.Connection) -> None:
        """Update story in database."""
        if self.is_locked:
            raise ValueError("Cannot modify a final published story. Unpublish first.")
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE stories SET title = ?, synopsis = ?, sort_order = ?, 
               status = ?, published_at = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (self.title, self.synopsis, self.sort_order, self.status,
             self.published_at.isoformat() if self.published_at else None, self.id)
        )
        conn.commit()
    
    def publish_rough(self, conn: sqlite3.Connection) -> None:
        """Mark story as rough published."""
        self.status = STATUS_ROUGH_PUBLISHED
        self.published_at = datetime.now()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE stories SET status = ?, published_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.status, self.published_at.isoformat(), self.id)
        )
        conn.commit()
    
    def publish_final(self, conn: sqlite3.Connection) -> None:
        """Mark story as final published (locks it)."""
        self.status = STATUS_FINAL_PUBLISHED
        self.published_at = datetime.now()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE stories SET status = ?, published_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.status, self.published_at.isoformat(), self.id)
        )
        conn.commit()
    
    def unpublish(self, conn: sqlite3.Connection) -> None:
        """Revert to draft status (unlocks if final)."""
        self.status = STATUS_DRAFT
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE stories SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.status, self.id)
        )
        conn.commit()
    
    def delete(self, conn: sqlite3.Connection) -> None:
        """Delete story from database."""
        if self.is_locked:
            raise ValueError("Cannot delete a final published story. Unpublish first.")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stories WHERE id = ?", (self.id,))
        conn.commit()
