"""
Unit tests for EncyclopediaService.

Tests all CRUD operations, search, and event emission for encyclopedia entries.
"""
import pytest
from events.events import EntryCreated, EntryUpdated, EntryDeleted, EntryOpened, EntryClosed


class TestEncyclopediaService:
    """Test cases for EncyclopediaService."""
    
    # =========================================================================
    # Create Tests
    # =========================================================================
    
    def test_create_entry(self, encyclopedia_service, sample_project, event_recorder):
        """Test creating a new encyclopedia entry."""
        event_recorder.clear()
        
        entry = encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Dragon",
            category="Creature",
            content="A fire-breathing mythical beast",
            tags="monster, flying, fire"
        )
        
        assert entry.id is not None
        assert entry.project_id == sample_project.id
        assert entry.name == "Dragon"
        assert entry.category == "Creature"
        assert entry.content == "A fire-breathing mythical beast"
        assert entry.tags == "monster, flying, fire"
    
    def test_create_entry_emits_event(self, encyclopedia_service, sample_project, event_recorder):
        """Test that creating an entry emits EntryCreated event."""
        event_recorder.clear()
        
        entry = encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Event Test",
            category="Character"
        )
        
        assert event_recorder.has_event(EntryCreated)
        events = event_recorder.get_events(EntryCreated)
        assert len(events) == 1
        assert events[0].entry_id == entry.id
        assert events[0].name == "Event Test"
        assert events[0].category == "Character"
    
    def test_create_entry_minimal(self, encyclopedia_service, sample_project):
        """Test creating an entry with minimal data."""
        entry = encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Simple Entry",
            category="Location"
        )
        
        assert entry.name == "Simple Entry"
        assert entry.category == "Location"
        assert entry.content == ""
        assert entry.tags == ""
    
    # =========================================================================
    # Read Tests
    # =========================================================================
    
    def test_list_entries_empty(self, encyclopedia_service, sample_project):
        """Test listing entries when none exist."""
        entries = encyclopedia_service.list_entries(sample_project.id)
        assert entries == []
    
    def test_list_entries(self, encyclopedia_service, sample_project):
        """Test listing multiple entries."""
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Hero", category="Character"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Castle", category="Location"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Magic Sword", category="Item"
        )
        
        entries = encyclopedia_service.list_entries(sample_project.id)
        
        assert len(entries) == 3
    
    def test_list_entries_by_category(self, encyclopedia_service, sample_project):
        """Test filtering entries by category."""
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Hero", category="Character"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Villain", category="Character"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Castle", category="Location"
        )
        
        characters = encyclopedia_service.list_entries(
            sample_project.id,
            category="Character"
        )
        
        assert len(characters) == 2
        assert all(e.category == "Character" for e in characters)
    
    def test_get_entry(self, encyclopedia_service, sample_project):
        """Test getting an entry by ID."""
        created = encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Get Test",
            category="Item",
            content="Test content"
        )
        
        fetched = encyclopedia_service.get_entry(created.id)
        
        assert fetched.id == created.id
        assert fetched.name == "Get Test"
        assert fetched.content == "Test content"
    
    def test_get_entry_not_found(self, encyclopedia_service):
        """Test getting a non-existent entry raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            encyclopedia_service.get_entry(99999)
    
    # =========================================================================
    # Update Tests
    # =========================================================================
    
    def test_update_entry_name(self, encyclopedia_service, sample_entry, event_recorder):
        """Test updating entry name."""
        event_recorder.clear()
        
        updated = encyclopedia_service.update_entry(
            sample_entry.id,
            name="New Name"
        )
        
        assert updated.name == "New Name"
        assert event_recorder.has_event(EntryUpdated)
    
    def test_update_entry_category(self, encyclopedia_service, sample_entry):
        """Test updating entry category."""
        updated = encyclopedia_service.update_entry(
            sample_entry.id,
            category="Location"
        )
        
        assert updated.category == "Location"
    
    def test_update_entry_content(self, encyclopedia_service, sample_entry):
        """Test updating entry content."""
        updated = encyclopedia_service.update_entry(
            sample_entry.id,
            content="Updated content here"
        )
        
        assert updated.content == "Updated content here"
    
    def test_update_entry_tags(self, encyclopedia_service, sample_entry):
        """Test updating entry tags."""
        updated = encyclopedia_service.update_entry(
            sample_entry.id,
            tags="new, tags, here"
        )
        
        assert updated.tags == "new, tags, here"
    
    def test_update_entry_not_found(self, encyclopedia_service):
        """Test updating a non-existent entry raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            encyclopedia_service.update_entry(99999, name="New")
    
    # =========================================================================
    # Delete Tests
    # =========================================================================
    
    def test_delete_entry(self, encyclopedia_service, sample_entry, event_recorder):
        """Test deleting an entry."""
        entry_id = sample_entry.id
        event_recorder.clear()
        
        encyclopedia_service.delete_entry(entry_id)
        
        with pytest.raises(ValueError, match="not found"):
            encyclopedia_service.get_entry(entry_id)
        
        assert event_recorder.has_event(EntryDeleted)
    
    def test_delete_entry_not_found(self, encyclopedia_service):
        """Test deleting a non-existent entry raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            encyclopedia_service.delete_entry(99999)
    
    # =========================================================================
    # Search Tests
    # =========================================================================
    
    def test_search_entries_by_name(self, encyclopedia_service, sample_project):
        """Test searching entries by name."""
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Dragon Lord", category="Character"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Dragon Cave", category="Location"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Magic Sword", category="Item"
        )
        
        results = encyclopedia_service.search_entries(sample_project.id, "Dragon")
        
        assert len(results) == 2
        assert all("Dragon" in e.name for e in results)
    
    def test_search_entries_by_content(self, encyclopedia_service, sample_project):
        """Test searching entries by content."""
        encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Hero",
            category="Character",
            content="A brave warrior from the northern kingdom"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Villain",
            category="Character",
            content="An evil sorcerer from the east"
        )
        
        results = encyclopedia_service.search_entries(sample_project.id, "northern")
        
        assert len(results) == 1
        assert results[0].name == "Hero"
    
    def test_search_entries_by_tags(self, encyclopedia_service, sample_project):
        """Test searching entries by tags."""
        encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Fire Dragon",
            category="Creature",
            tags="monster, fire, flying"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id,
            name="Ice Dragon",
            category="Creature",
            tags="monster, ice, flying"
        )
        
        results = encyclopedia_service.search_entries(sample_project.id, "fire")
        
        assert len(results) == 1
        assert results[0].name == "Fire Dragon"
    
    def test_search_entries_no_results(self, encyclopedia_service, sample_project):
        """Test searching with no matching results."""
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Hero", category="Character"
        )
        
        results = encyclopedia_service.search_entries(sample_project.id, "nonexistent")
        
        assert len(results) == 0
    
    # =========================================================================
    # Category List Tests
    # =========================================================================
    
    def test_list_categories(self, encyclopedia_service, sample_project):
        """Test listing all categories in use."""
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Hero", category="Character"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Castle", category="Location"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Villain", category="Character"
        )
        encyclopedia_service.create_entry(
            project_id=sample_project.id, name="Sword", category="Item"
        )
        
        categories = encyclopedia_service.list_categories(sample_project.id)
        
        # Service returns default categories plus used ones
        assert "Character" in categories
        assert "Location" in categories
        assert "Item" in categories
        # Should include defaults too
        assert len(categories) >= 3
    
    def test_list_categories_empty(self, encyclopedia_service, sample_project):
        """Test listing categories when no entries exist returns defaults."""
        categories = encyclopedia_service.list_categories(sample_project.id)
        # Returns default categories even when no entries
        assert len(categories) >= 1
        assert "Character" in categories  # Default category
    
    # =========================================================================
    # Open/Close Tests
    # =========================================================================
    
    def test_open_entry(self, encyclopedia_service, sample_entry, event_recorder):
        """Test opening an entry emits event."""
        event_recorder.clear()
        
        encyclopedia_service.open_entry(sample_entry.id)
        
        assert event_recorder.has_event(EntryOpened)
    
    def test_close_entry(self, encyclopedia_service, sample_entry, event_recorder):
        """Test closing an entry emits event."""
        event_recorder.clear()
        
        encyclopedia_service.close_entry(sample_entry.id)
        
        assert event_recorder.has_event(EntryClosed)
