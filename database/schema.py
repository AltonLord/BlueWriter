"""
Database schema definition for BlueWriter.
Defines all tables with proper relationships.
"""
import json
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
    story_id INTEGER,
    project_id INTEGER,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    board_x REAL DEFAULT 100.0,
    board_y REAL DEFAULT 100.0,
    sort_order INTEGER DEFAULT 0,
    color TEXT DEFAULT '#FFFF88',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
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

    # --- BLU-002: Unified Canvas Migrations ---

    # Add story visual representation fields
    cursor.execute("PRAGMA table_info(stories)")
    story_cols = [col[1] for col in cursor.fetchall()]

    if 'representation_type' not in story_cols:
        cursor.execute("ALTER TABLE stories ADD COLUMN representation_type TEXT DEFAULT 'box'")
        connection.commit()

    if 'bounding_data' not in story_cols:
        cursor.execute("ALTER TABLE stories ADD COLUMN bounding_data TEXT")
        connection.commit()

    if 'outline_color' not in story_cols:
        cursor.execute("ALTER TABLE stories ADD COLUMN outline_color TEXT DEFAULT '#4A90D9'")
        connection.commit()

    # Make chapters.story_id nullable and add project_id
    cursor.execute("PRAGMA table_info(chapters)")
    chapter_cols = {col[1]: col for col in cursor.fetchall()}

    needs_chapter_migration = False
    if 'story_id' in chapter_cols:
        # notnull flag is index 3: 1 = NOT NULL, 0 = nullable
        if chapter_cols['story_id'][3] == 1:
            needs_chapter_migration = True
    if 'project_id' not in chapter_cols:
        needs_chapter_migration = True

    if needs_chapter_migration:
        # SQLite doesn't support ALTER COLUMN, so we recreate the table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER,
                project_id INTEGER,
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                board_x REAL DEFAULT 100.0,
                board_y REAL DEFAULT 100.0,
                sort_order INTEGER DEFAULT 0,
                color TEXT DEFAULT '#FFFF88',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE SET NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        # Copy data, inserting NULL for project_id if column didn't exist
        if 'project_id' in chapter_cols:
            cursor.execute("""
                INSERT INTO chapters_new
                SELECT id, story_id, project_id, title, summary, content, board_x, board_y,
                       sort_order, color, created_at, updated_at
                FROM chapters
            """)
        else:
            cursor.execute("""
                INSERT INTO chapters_new
                SELECT id, story_id, NULL, title, summary, content, board_x, board_y,
                       sort_order, color, created_at, updated_at
                FROM chapters
            """)
        cursor.execute("DROP TABLE chapters")
        cursor.execute("ALTER TABLE chapters_new RENAME TO chapters")
        connection.commit()

    # Backfill project_id on chapters from their story's project
    cursor.execute("""
        UPDATE chapters
        SET project_id = (
            SELECT stories.project_id
            FROM stories
            WHERE stories.id = chapters.story_id
        )
        WHERE project_id IS NULL AND story_id IS NOT NULL
    """)
    connection.commit()

    # Auto-create bounding boxes for existing stories that have chapters but no bounding_data
    cursor.execute("""
        SELECT s.id, MIN(c.board_x), MIN(c.board_y), MAX(c.board_x), MAX(c.board_y)
        FROM stories s
        JOIN chapters c ON c.story_id = s.id
        WHERE s.bounding_data IS NULL
        GROUP BY s.id
    """)
    rows = cursor.fetchall()
    for story_id, min_x, min_y, max_x, max_y in rows:
        if min_x is not None:
            padding = 80
            bounding_data = json.dumps({
                "x1": min_x - padding,
                "y1": min_y - padding,
                "x2": max_x + 150 + padding,
                "y2": max_y + 100 + padding
            })
            cursor.execute(
                "UPDATE stories SET bounding_data = ?, representation_type = 'box' WHERE id = ?",
                (bounding_data, story_id)
            )
    connection.commit()

def drop_all_tables(connection: sqlite3.Connection) -> None:
    """Drop all tables (for testing/reset)."""
    cursor = connection.cursor()
    cursor.execute("DROP TABLE IF EXISTS chapter_characters")
    cursor.execute("DROP TABLE IF EXISTS characters")
    cursor.execute("DROP TABLE IF EXISTS chapters_new")
    cursor.execute("DROP TABLE IF EXISTS chapters")
    cursor.execute("DROP TABLE IF EXISTS stories")
    cursor.execute("DROP TABLE IF EXISTS projects")
    connection.commit()
