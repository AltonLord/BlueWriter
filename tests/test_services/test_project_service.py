"""
Unit tests for ProjectService.

Tests all CRUD operations and event emission for projects.
"""
import pytest
from events.events import ProjectCreated, ProjectUpdated, ProjectDeleted, ProjectOpened


class TestProjectService:
    """Test cases for ProjectService."""
    
    # =========================================================================
    # Create Tests
    # =========================================================================
    
    def test_create_project(self, project_service, event_recorder):
        """Test creating a new project."""
        project = project_service.create_project(
            name="My Novel",
            description="An epic tale"
        )
        
        assert project.id is not None
        assert project.name == "My Novel"
        assert project.description == "An epic tale"
        assert project.created_at is not None
        assert project.updated_at is not None
    
    def test_create_project_emits_event(self, project_service, event_recorder):
        """Test that creating a project emits ProjectCreated event."""
        project = project_service.create_project(name="Event Test")
        
        assert event_recorder.has_event(ProjectCreated)
        events = event_recorder.get_events(ProjectCreated)
        assert len(events) == 1
        assert events[0].project_id == project.id
        assert events[0].name == "Event Test"
    
    def test_create_project_empty_name_fails(self, project_service):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            project_service.create_project(name="")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            project_service.create_project(name="   ")
    
    def test_create_project_strips_whitespace(self, project_service):
        """Test that project name is stripped of whitespace."""
        project = project_service.create_project(name="  Padded Name  ")
        assert project.name == "Padded Name"
    
    # =========================================================================
    # Read Tests
    # =========================================================================
    
    def test_list_projects_empty(self, project_service):
        """Test listing projects when none exist."""
        projects = project_service.list_projects()
        assert projects == []
    
    def test_list_projects(self, project_service):
        """Test listing multiple projects."""
        project_service.create_project(name="Project A")
        project_service.create_project(name="Project B")
        project_service.create_project(name="Project C")
        
        projects = project_service.list_projects()
        
        assert len(projects) == 3
        names = [p.name for p in projects]
        assert "Project A" in names
        assert "Project B" in names
        assert "Project C" in names
    
    def test_get_project(self, project_service):
        """Test getting a project by ID."""
        created = project_service.create_project(
            name="Get Test",
            description="Test description"
        )
        
        fetched = project_service.get_project(created.id)
        
        assert fetched.id == created.id
        assert fetched.name == "Get Test"
        assert fetched.description == "Test description"
    
    def test_get_project_not_found(self, project_service):
        """Test getting a non-existent project raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            project_service.get_project(99999)
    
    # =========================================================================
    # Update Tests
    # =========================================================================
    
    def test_update_project_name(self, project_service, event_recorder):
        """Test updating project name."""
        project = project_service.create_project(name="Original")
        event_recorder.clear()
        
        updated = project_service.update_project(project.id, name="Updated")
        
        assert updated.name == "Updated"
        assert event_recorder.has_event(ProjectUpdated)
        event = event_recorder.get_events(ProjectUpdated)[0]
        assert "name" in event.fields_changed
    
    def test_update_project_description(self, project_service):
        """Test updating project description."""
        project = project_service.create_project(name="Test", description="Old")
        
        updated = project_service.update_project(
            project.id,
            description="New description"
        )
        
        assert updated.description == "New description"
        assert updated.name == "Test"  # Unchanged
    
    def test_update_project_both_fields(self, project_service, event_recorder):
        """Test updating both name and description."""
        project = project_service.create_project(name="Old", description="Old desc")
        event_recorder.clear()
        
        updated = project_service.update_project(
            project.id,
            name="New",
            description="New desc"
        )
        
        assert updated.name == "New"
        assert updated.description == "New desc"
        
        event = event_recorder.get_events(ProjectUpdated)[0]
        assert "name" in event.fields_changed
        assert "description" in event.fields_changed
    
    def test_update_project_empty_name_fails(self, project_service):
        """Test that updating with empty name raises ValueError."""
        project = project_service.create_project(name="Test")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            project_service.update_project(project.id, name="")
    
    def test_update_project_not_found(self, project_service):
        """Test updating a non-existent project raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            project_service.update_project(99999, name="New")
    
    def test_update_no_changes(self, project_service, event_recorder):
        """Test that updating with no changes doesn't emit event."""
        project = project_service.create_project(name="Test")
        event_recorder.clear()
        
        # Call update without any changes
        project_service.update_project(project.id)
        
        assert not event_recorder.has_event(ProjectUpdated)
    
    # =========================================================================
    # Delete Tests
    # =========================================================================
    
    def test_delete_project(self, project_service, event_recorder):
        """Test deleting a project."""
        project = project_service.create_project(name="To Delete")
        project_id = project.id
        event_recorder.clear()
        
        project_service.delete_project(project_id)
        
        # Should not be found anymore
        with pytest.raises(ValueError, match="not found"):
            project_service.get_project(project_id)
        
        # Should have emitted event
        assert event_recorder.has_event(ProjectDeleted)
        event = event_recorder.get_events(ProjectDeleted)[0]
        assert event.project_id == project_id
    
    def test_delete_project_not_found(self, project_service):
        """Test deleting a non-existent project raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            project_service.delete_project(99999)
    
    # =========================================================================
    # Open Tests
    # =========================================================================
    
    def test_open_project(self, project_service, event_recorder):
        """Test opening a project emits ProjectOpened event."""
        project = project_service.create_project(name="Open Me")
        event_recorder.clear()
        
        result = project_service.open_project(project.id)
        
        assert result.id == project.id
        assert event_recorder.has_event(ProjectOpened)
        event = event_recorder.get_events(ProjectOpened)[0]
        assert event.project_id == project.id
    
    def test_open_project_not_found(self, project_service):
        """Test opening a non-existent project raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            project_service.open_project(99999)
