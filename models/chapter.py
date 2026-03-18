"""
Chapter model for BlueWriter.
Represents a sticky note on the timeline canvas.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import sqlite3

# Explicit column list for consistent ordering
CHAPTER_COLUMNS = "id, story_id, project_id, title, summary, content, board_x, board_y, sort_order, color, created_at, updated_at"


@dataclass
class Chapter:
    """Represents a sticky note on the timeline canvas."""
    id: Optional[int] = None
    story_id: Optional[int] = None
    project_id: Optional[int] = None
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
    def _from_row(cls, row) -> "Chapter":
        """Create Chapter from database row (expects columns in CHAPTER_COLUMNS order)."""
        return cls(
            id=row[0],
            story_id=row[1],
            project_id=row[2],
            title=row[3],
            summary=row[4],
            content=row[5],
            board_x=row[6],
            board_y=row[7],
            sort_order=row[8],
            color=row[9],
            created_at=datetime.fromisoformat(row[10]) if row[10] else None,
            updated_at=datetime.fromisoformat(row[11]) if row[11] else None,
        )

    @classmethod
    def create(cls, conn: sqlite3.Connection, story_id: Optional[int], title: str,
               summary: str = "", content: str = "",
               project_id: Optional[int] = None) -> "Chapter":
        """Insert new chapter and return instance."""
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chapters (story_id, project_id, title, summary, content) VALUES (?, ?, ?, ?, ?)",
            (story_id, project_id, title, summary, content)
        )
        conn.commit()

        # Get the inserted chapter
        chapter_id = cursor.lastrowid
        return cls.get_by_id(conn, chapter_id)

    @classmethod
    def get_by_id(cls, conn: sqlite3.Connection, chapter_id: int) -> Optional["Chapter"]:
        """Retrieve chapter by ID."""
        cursor = conn.cursor()
        cursor.execute(f"SELECT {CHAPTER_COLUMNS} FROM chapters WHERE id = ?", (chapter_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return cls._from_row(row)

    @classmethod
    def get_by_story(cls, conn: sqlite3.Connection, story_id: int) -> List["Chapter"]:
        """Retrieve all chapters for a story."""
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {CHAPTER_COLUMNS} FROM chapters WHERE story_id = ? ORDER BY sort_order, created_at DESC",
            (story_id,)
        )
        rows = cursor.fetchall()
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_by_project(cls, conn: sqlite3.Connection, project_id: int) -> List["Chapter"]:
        """Retrieve all chapters for a project (across all stories + orphans)."""
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {CHAPTER_COLUMNS} FROM chapters WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,)
        )
        rows = cursor.fetchall()
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_all(cls, conn: sqlite3.Connection) -> List["Chapter"]:
        """Retrieve all chapters."""
        cursor = conn.cursor()
        cursor.execute(f"SELECT {CHAPTER_COLUMNS} FROM chapters ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [cls._from_row(row) for row in rows]

    def update(self, conn: sqlite3.Connection) -> None:
        """Update chapter in database."""
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE chapters SET story_id = ?, project_id = ?, title = ?, summary = ?,
               content = ?, board_x = ?, board_y = ?, sort_order = ?, color = ?,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (self.story_id, self.project_id, self.title, self.summary, self.content,
             self.board_x, self.board_y, self.sort_order, self.color, self.id)
        )
        conn.commit()

    def delete(self, conn: sqlite3.Connection) -> None:
        """Delete chapter from database."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chapters WHERE id = ?", (self.id,))
        conn.commit()
