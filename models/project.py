"""
Project model for BlueWriter.
Represents a writing project (series or standalone).
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import sqlite3

@dataclass
class Project:
    """Represents a writing project (series or standalone)."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, conn: sqlite3.Connection, name: str, description: str = "") -> "Project":
        """Insert new project and return instance."""
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description)
        )
        conn.commit()
        
        # Get the inserted project
        project_id = cursor.lastrowid
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        return cls(
            id=row[0],
            name=row[1],
            description=row[2],
            created_at=datetime.fromisoformat(row[3]) if row[3] else None,
            updated_at=datetime.fromisoformat(row[4]) if row[4] else None
        )
    
    @classmethod
    def get_by_id(cls, conn: sqlite3.Connection, project_id: int) -> Optional["Project"]:
        """Retrieve project by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        return cls(
            id=row[0],
            name=row[1],
            description=row[2],
            created_at=datetime.fromisoformat(row[3]) if row[3] else None,
            updated_at=datetime.fromisoformat(row[4]) if row[4] else None
        )
    
    @classmethod
    def get_all(cls, conn: sqlite3.Connection) -> List["Project"]:
        """Retrieve all projects."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            projects.append(cls(
                id=row[0],
                name=row[1],
                description=row[2],
                created_at=datetime.fromisoformat(row[3]) if row[3] else None,
                updated_at=datetime.fromisoformat(row[4]) if row[4] else None
            ))
        
        return projects
    
    def update(self, conn: sqlite3.Connection) -> None:
        """Update project in database."""
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE projects SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.name, self.description, self.id)
        )
        conn.commit()
    
    def delete(self, conn: sqlite3.Connection) -> None:
        """Delete project from database."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (self.id,))
        conn.commit()
