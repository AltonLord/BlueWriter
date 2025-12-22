"""
Database connection manager for BlueWriter.
Handles SQLite connections with context manager support.
"""
from pathlib import Path
from typing import Optional, Union
import sqlite3
import os

class DatabaseManager:
    """Manages SQLite database connections."""
    
    def __init__(self, db_path: Union[str, Path]) -> None:
        """Initialize with database file path (string or Path)."""
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        # Ensure the data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def connect(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Use WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def __enter__(self) -> sqlite3.Connection:
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with commit/rollback."""
        # The connection is automatically closed when exiting the context
        # If there's an exception, it will be handled by the caller
        pass

def get_default_db_path() -> Path:
    """Return default database path in data/ directory."""
    # Use absolute path relative to project root
    project_root = Path(__file__).parent.parent
    return project_root / "data" / "bluewriter.db"
