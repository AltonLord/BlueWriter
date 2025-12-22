"""
Chapter model for BlueWriter.
Represents a sticky note on the timeline canvas.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import sqlite3

@dataclass
class Chapter:
    """Represents a sticky note on the timeline canvas."""
    id: Optional[int] = None
    story_id: int = 0
    title: str = ""
    summary: str = ""
    content: str = ""
    board_x: float = 100.0
    board_y: float = 100.0
    sort_order: int = 0
    color: str = "#FFFF88"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, conn: sqlite3.Connection, story_id: int, title: str, summary: str = "", content: str = "") -> "Chapter":
        """Insert new chapter and return instance."""
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chapters (story_id, title, summary, content) VALUES (?, ?, ?, ?)",
            (story_id, title, summary, content)
        )
        conn.commit()
        
        # Get the inserted chapter
        chapter_id = cursor.lastrowid
        cursor.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,))
        row = cursor.fetchone()
        
        return cls(
            id=row[0],
            story_id=row[1],
            title=row[2],
            summary=row[3],
            content=row[4],
            board_x=row[5],
            board_y=row[6],
            sort_order=row[7],
            color=row[8],
            created_at=datetime.fromisoformat(row[9]) if row[9] else None,
            updated_at=datetime.fromisoformat(row[10]) if row[10] else None
        )
    
    @classmethod
    def get_by_id(cls, conn: sqlite3.Connection, chapter_id: int) -> Optional["Chapter"]:
        """Retrieve chapter by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        return cls(
            id=row[0],
            story_id=row[1],
            title=row[2],
            summary=row[3],
            content=row[4],
            board_x=row[5],
            board_y=row[6],
            sort_order=row[7],
            color=row[8],
            created_at=datetime.fromisoformat(row[9]) if row[9] else None,
            updated_at=datetime.fromisoformat(row[10]) if row[10] else None
        )
    
    @classmethod
    def get_by_story(cls, conn: sqlite3.Connection, story_id: int) -> List["Chapter"]:
        """Retrieve all chapters for a story."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chapters WHERE story_id = ? ORDER BY sort_order, created_at DESC", (story_id,))
        rows = cursor.fetchall()
        
        chapters = []
        for row in rows:
            chapters.append(cls(
                id=row[0],
                story_id=row[1],
                title=row[2],
                summary=row[3],
                content=row[4],
                board_x=row[5],
                board_y=row[6],
                sort_order=row[7],
                color=row[8],
                created_at=datetime.fromisoformat(row[9]) if row[9] else None,
                updated_at=datetime.fromisoformat(row[10]) if row[10] else None
            ))
        
        return chapters
    
    @classmethod
    def get_all(cls, conn: sqlite3.Connection) -> List["Chapter"]:
        """Retrieve all chapters."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chapters ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        chapters = []
        for row in rows:
            chapters.append(cls(
                id=row[0],
                story_id=row[1],
                title=row[2],
                summary=row[3],
                content=row[4],
                board_x=row[5],
                board_y=row[6],
                sort_order=row[7],
                color=row[8],
                created_at=datetime.fromisoformat(row[9]) if row[9] else None,
                updated_at=datetime.fromisoformat(row[10]) if row[10] else None
            ))
        
        return chapters
    
    def update(self, conn: sqlite3.Connection) -> None:
        """Update chapter in database."""
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chapters SET title = ?, summary = ?, content = ?, board_x = ?, board_y = ?, sort_order = ?, color = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.title, self.summary, self.content, self.board_x, self.board_y, self.sort_order, self.color, self.id)
        )
        conn.commit()
    
    def delete(self, conn: sqlite3.Connection) -> None:
        """Delete chapter from database."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chapters WHERE id = ?", (self.id,))
        conn.commit()
