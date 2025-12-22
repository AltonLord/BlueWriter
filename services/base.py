"""
Base service class for BlueWriter services.

All services inherit from BaseService which provides:
- Database connection management
- Event bus reference for publishing events
"""
from typing import TYPE_CHECKING
import sqlite3

from database.connection import DatabaseManager

if TYPE_CHECKING:
    from events.event_bus import EventBus


class BaseService:
    """Base class for all BlueWriter services.
    
    Provides common functionality for database access and event publishing.
    Services should never import Qt or any UI framework.
    
    Attributes:
        db_path: Path to the SQLite database file
        event_bus: EventBus instance for publishing events
    """
    
    def __init__(self, db_path: str, event_bus: 'EventBus') -> None:
        """Initialize the service.
        
        Args:
            db_path: Path to the SQLite database file
            event_bus: EventBus instance for publishing events
        """
        self.db_path = db_path
        self.event_bus = event_bus
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection for this operation.
        
        Creates a new connection for each call to ensure thread safety.
        Caller is responsible for closing the connection.
        
        Returns:
            SQLite connection with foreign keys enabled
            
        Example:
            conn = self._get_connection()
            try:
                # do work
                conn.commit()
            finally:
                conn.close()
        """
        db_manager = DatabaseManager(self.db_path)
        return db_manager.connect()
