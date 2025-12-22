"""
Database schema definition for BlueWriter.
Defines all tables with proper relationships.
"""
import sqlite3

# SQL statements for creating tables
PROJECTS_TABLE_SQL = """
-- Projects table (series or standalone book container)
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

STORIES_TABLE_SQL = """
-- Stories table (individual books within a project)
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    synopsis TEXT,
    sort_order INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
"""

CHAPTERS_TABLE_SQL = """
-- Chapters table (the sticky notes)
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    board_x REAL DEFAULT 100.0,
    board_y REAL DEFAULT 100.0,
    sort_order INTEGER DEFAULT 0,
    color TEXT DEFAULT '#FFFF88',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
);
"""

CHARACTERS_TABLE_SQL = """
-- Characters table (shared across stories in a project)
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
"""

CHAPTER_CHARACTERS_TABLE_SQL = """
-- Character appearances (which chapters feature which characters)
CREATE TABLE IF NOT EXISTS chapter_characters (
    chapter_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    PRIMARY KEY (chapter_id, character_id),
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);
"""

ENCYCLOPEDIA_ENTRIES_TABLE_SQL = """
-- Encyclopedia entries for world-building (project-level)
CREATE TABLE IF NOT EXISTS encyclopedia_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    category TEXT NOT NULL DEFAULT 'General',
    name TEXT NOT NULL,
    content TEXT,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
"""

def create_all_tables(connection: sqlite3.Connection) -> None:
    """Create all tables if they don't exist."""
    cursor = connection.cursor()
    cursor.execute(PROJECTS_TABLE_SQL)
    cursor.execute(STORIES_TABLE_SQL)
    cursor.execute(CHAPTERS_TABLE_SQL)
    cursor.execute(CHARACTERS_TABLE_SQL)
    cursor.execute(CHAPTER_CHARACTERS_TABLE_SQL)
    cursor.execute(ENCYCLOPEDIA_ENTRIES_TABLE_SQL)
    connection.commit()
    
    # Run migrations for existing databases
    migrate_database(connection)


def migrate_database(connection: sqlite3.Connection) -> None:
    """Apply migrations to existing databases."""
    cursor = connection.cursor()
    
    # Check if stories table has status column
    cursor.execute("PRAGMA table_info(stories)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'status' not in columns:
        cursor.execute("ALTER TABLE stories ADD COLUMN status TEXT DEFAULT 'draft'")
        connection.commit()
    
    if 'published_at' not in columns:
        cursor.execute("ALTER TABLE stories ADD COLUMN published_at TIMESTAMP")
        connection.commit()

def drop_all_tables(connection: sqlite3.Connection) -> None:
    """Drop all tables (for testing/reset)."""
    cursor = connection.cursor()
    cursor.execute("DROP TABLE IF EXISTS chapter_characters")
    cursor.execute("DROP TABLE IF EXISTS characters")
    cursor.execute("DROP TABLE IF EXISTS chapters")
    cursor.execute("DROP TABLE IF EXISTS stories")
    cursor.execute("DROP TABLE IF EXISTS projects")
    connection.commit()
