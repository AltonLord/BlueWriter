"""
Project service for BlueWriter.

Handles all project-related business logic and database operations.
Emits events for state changes that UI can subscribe to.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from services.base import BaseService
from events.event_bus import EventBus
from events.events import (
    ProjectCreated,
    ProjectUpdated,
    ProjectDeleted,
    ProjectOpened,
)
from models.project import Project


@dataclass
class ProjectDTO:
    """Data transfer object for projects.
    
    Used to pass project data between layers without
    exposing the database model directly.
    """
    id: int
    name: str
    description: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ProjectService(BaseService):
    """Service for managing writing projects.
    
    Provides CRUD operations for projects and emits
    events for all state changes.
    
    Example:
        event_bus = EventBus()
        service = ProjectService("/path/to/db", event_bus)
        
        # Create a project
        project = service.create_project("My Novel", "A story about...")
        
        # List all projects
        projects = service.list_projects()
    """
    
    def __init__(self, db_path: str, event_bus: EventBus) -> None:
        """Initialize the project service.
        
        Args:
            db_path: Path to the SQLite database
            event_bus: EventBus for publishing events
        """
        super().__init__(db_path, event_bus)
    
    def _project_to_dto(self, project: Project) -> ProjectDTO:
        """Convert a Project model to ProjectDTO.
        
        Args:
            project: Project model instance
            
        Returns:
            ProjectDTO with the project data
        """
        return ProjectDTO(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    
    def list_projects(self) -> List[ProjectDTO]:
        """Get all projects.
        
        Returns:
            List of ProjectDTO objects, ordered by created_at descending
        """
        conn = self._get_connection()
        try:
            projects = Project.get_all(conn)
            return [self._project_to_dto(p) for p in projects]
        finally:
            conn.close()
    
    def get_project(self, project_id: int) -> ProjectDTO:
        """Get a project by ID.
        
        Args:
            project_id: The project's database ID
            
        Returns:
            ProjectDTO with the project data
            
        Raises:
            ValueError: If project not found
        """
        conn = self._get_connection()
        try:
            project = Project.get_by_id(conn, project_id)
            if project is None:
                raise ValueError(f"Project {project_id} not found")
            return self._project_to_dto(project)
        finally:
            conn.close()
    
    def create_project(self, name: str, description: str = "") -> ProjectDTO:
        """Create a new project.
        
        Args:
            name: Project name (required)
            description: Optional project description
            
        Returns:
            ProjectDTO with the created project data
            
        Raises:
            ValueError: If name is empty
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        
        conn = self._get_connection()
        try:
            project = Project.create(conn, name.strip(), description)
            dto = self._project_to_dto(project)
            
            # Emit event
            self.event_bus.publish(ProjectCreated(
                project_id=dto.id,
                name=dto.name,
            ))
            
            return dto
        finally:
            conn.close()
    
    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ProjectDTO:
        """Update an existing project.
        
        Only provided fields will be updated.
        
        Args:
            project_id: The project's database ID
            name: New name (optional)
            description: New description (optional)
            
        Returns:
            ProjectDTO with the updated project data
            
        Raises:
            ValueError: If project not found or name is empty
        """
        conn = self._get_connection()
        try:
            project = Project.get_by_id(conn, project_id)
            if project is None:
                raise ValueError(f"Project {project_id} not found")
            
            fields_changed = []
            
            if name is not None:
                if not name.strip():
                    raise ValueError("Project name cannot be empty")
                project.name = name.strip()
                fields_changed.append("name")
            
            if description is not None:
                project.description = description
                fields_changed.append("description")
            
            if fields_changed:
                project.update(conn)
                
                # Emit event
                self.event_bus.publish(ProjectUpdated(
                    project_id=project_id,
                    fields_changed=fields_changed,
                ))
            
            # Re-fetch to get updated timestamp
            project = Project.get_by_id(conn, project_id)
            return self._project_to_dto(project)
        finally:
            conn.close()
    
    def delete_project(self, project_id: int) -> None:
        """Delete a project.
        
        This will also delete all stories and chapters in the project
        due to foreign key cascades.
        
        Args:
            project_id: The project's database ID
            
        Raises:
            ValueError: If project not found
        """
        conn = self._get_connection()
        try:
            project = Project.get_by_id(conn, project_id)
            if project is None:
                raise ValueError(f"Project {project_id} not found")
            
            project.delete(conn)
            
            # Emit event
            self.event_bus.publish(ProjectDeleted(
                project_id=project_id,
            ))
        finally:
            conn.close()
    
    def open_project(self, project_id: int) -> ProjectDTO:
        """Open/select a project in the UI.
        
        This emits a ProjectOpened event that the UI can
        respond to by loading the project's stories.
        
        Args:
            project_id: The project's database ID
            
        Returns:
            ProjectDTO with the project data
            
        Raises:
            ValueError: If project not found
        """
        dto = self.get_project(project_id)  # Validates existence
        
        # Emit event
        self.event_bus.publish(ProjectOpened(
            project_id=project_id,
        ))
        
        return dto
