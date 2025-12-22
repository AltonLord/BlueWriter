"""
Character model for BlueWriter.
Represents a character shared across stories in a project.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import sqlite3

@dataclass
class Character:
    """Represents a character shared across stories in a project."""
    id: Optional[int] = None
    project_id: int = 0
    name: str = ""
    description: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, conn: sqlite3.Connection, project_id: int, name: str, description: str = "", notes: str = "") -> "Character":
        """Insert new character and return instance."""
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO characters (project_id, name, description, notes) VALUES (?, ?, ?, ?)",
            (project_id, name, description, notes)
        )
        conn.commit()
        
        # Get the inserted character
        character_id = cursor.lastrowid
        cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = cursor.fetchone()
        
        return cls(
            id=row[0],
            project_id=row[1],
            name=row[2],
            description=row[3],
            notes=row[4],
            created_at=datetime.fromisoformat(row[5]) if row[5] else None,
            updated_at=datetime.fromisoformat(row[6]) if row[6] else None
        )
    
    @classmethod
    def get_by_id(cls, conn: sqlite3.Connection, character_id: int) -> Optional["Character"]:
        """Retrieve character by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        return cls(
            id=row[0],
            project_id=row[1],
            name=row[2],
            description=row[3],
            notes=row[4],
            created_at=datetime.fromisoformat(row[5]) if row[5] else None,
            updated_at=datetime.fromisoformat(row[6]) if row[6] else None
        )
    
    @classmethod
    def get_by_project(cls, conn: sqlite3.Connection, project_id: int) -> List["Character"]:
        """Retrieve all characters for a project."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
        rows = cursor.fetchall()
        
        characters = []
        for row in rows:
            characters.append(cls(
                id=row[0],
                project_id=row[1],
                name=row[2],
                description=row[3],
                notes=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                updated_at=datetime.fromisoformat(row[6]) if row[6] else None
            ))
        
        return characters
    
    @classmethod
    def get_all(cls, conn: sqlite3.Connection) -> List["Character"]:
        """Retrieve all characters."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM characters ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        characters = []
        for row in rows:
            characters.append(cls(
                id=row[0],
                project_id=row[1],
                name=row[2],
                description=row[3],
                notes=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                updated_at=datetime.fromisoformat(row[6]) if row[6] else None
            ))
        
        return characters
    
    def update(self, conn: sqlite3.Connection) -> None:
        """Update character in database."""
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE characters SET name = ?, description = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.name, self.description, self.notes, self.id)
        )
        conn.commit()
    
    def delete(self, conn: sqlite3.Connection) -> None:
        """Delete character from database."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM characters WHERE id = ?", (self.id,))
        conn.commit()
