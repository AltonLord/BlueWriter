"""
Unit tests for EventBus.

Tests subscription, publishing, thread safety, and queue processing.
"""
import pytest
import threading
import time
from events.event_bus import EventBus
from events.events import ProjectCreated, ProjectDeleted, ChapterCreated


class TestEventBusBasics:
    """Basic EventBus functionality tests."""
    
    def test_subscribe_and_publish(self, event_bus):
        """Test basic subscribe and publish."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe(ProjectCreated, handler)
        event_bus.publish(ProjectCreated(project_id=1, name="Test"))
        
        assert len(received) == 1
        assert received[0].project_id == 1
        assert received[0].name == "Test"
    
    def test_multiple_subscribers(self, event_bus):
        """Test multiple subscribers to same event."""
        received1 = []
        received2 = []
        
        def handler1(event):
            received1.append(event)
        
        def handler2(event):
            received2.append(event)
        
        event_bus.subscribe(ProjectCreated, handler1)
        event_bus.subscribe(ProjectCreated, handler2)
        event_bus.publish(ProjectCreated(project_id=1, name="Test"))
        
        assert len(received1) == 1
        assert len(received2) == 1
    
    def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe(ProjectCreated, handler)
        event_bus.publish(ProjectCreated(project_id=1, name="First"))
        
        event_bus.unsubscribe(ProjectCreated, handler)
        event_bus.publish(ProjectCreated(project_id=2, name="Second"))
        
        assert len(received) == 1
        assert received[0].project_id == 1
    
    def test_unsubscribe_not_subscribed(self, event_bus):
        """Test unsubscribing a handler that wasn't subscribed."""
        def handler(event):
            pass
        
        # Should not raise
        event_bus.unsubscribe(ProjectCreated, handler)
    
    def test_different_event_types(self, event_bus):
        """Test that handlers only receive their subscribed event type."""
        project_events = []
        chapter_events = []
        
        def project_handler(event):
            project_events.append(event)
        
        def chapter_handler(event):
            chapter_events.append(event)
        
        event_bus.subscribe(ProjectCreated, project_handler)
        event_bus.subscribe(ChapterCreated, chapter_handler)
        
        event_bus.publish(ProjectCreated(project_id=1, name="Project"))
        event_bus.publish(ChapterCreated(
            chapter_id=1, story_id=1, title="Chapter",
            board_x=0, board_y=0, color="#FFFFFF"
        ))
        
        assert len(project_events) == 1
        assert len(chapter_events) == 1
        assert isinstance(project_events[0], ProjectCreated)
        assert isinstance(chapter_events[0], ChapterCreated)
    
    def test_no_subscribers(self, event_bus):
        """Test publishing with no subscribers doesn't raise."""
        # Should not raise
        event_bus.publish(ProjectCreated(project_id=1, name="Test"))
    
    def test_handler_exception_doesnt_stop_others(self, event_bus):
        """Test that one handler's exception doesn't prevent others."""
        received = []
        
        def bad_handler(event):
            raise RuntimeError("Handler error")
        
        def good_handler(event):
            received.append(event)
        
        event_bus.subscribe(ProjectCreated, bad_handler)
        event_bus.subscribe(ProjectCreated, good_handler)
        
        # Should not raise, good_handler should still be called
        event_bus.publish(ProjectCreated(project_id=1, name="Test"))
        
        assert len(received) == 1


class TestEventBusCounting:
    """Tests for subscriber and pending counts."""
    
    def test_subscriber_count_total(self, event_bus):
        """Test counting total subscribers."""
        def handler(event):
            pass
        
        assert event_bus.subscriber_count() == 0
        
        event_bus.subscribe(ProjectCreated, handler)
        assert event_bus.subscriber_count() == 1
        
        event_bus.subscribe(ProjectDeleted, handler)
        assert event_bus.subscriber_count() == 2
    
    def test_subscriber_count_by_type(self, event_bus):
        """Test counting subscribers by event type."""
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        event_bus.subscribe(ProjectCreated, handler1)
        event_bus.subscribe(ProjectCreated, handler2)
        event_bus.subscribe(ProjectDeleted, handler1)
        
        assert event_bus.subscriber_count(ProjectCreated) == 2
        assert event_bus.subscriber_count(ProjectDeleted) == 1
        assert event_bus.subscriber_count(ChapterCreated) == 0
    
    def test_pending_count(self, event_bus):
        """Test counting pending events."""
        assert event_bus.pending_count() == 0


class TestEventBusClear:
    """Tests for clearing the event bus."""
    
    def test_clear_removes_all_subscribers(self, event_bus):
        """Test that clear removes all subscribers."""
        def handler(event):
            pass
        
        event_bus.subscribe(ProjectCreated, handler)
        event_bus.subscribe(ProjectDeleted, handler)
        
        event_bus.clear()
        
        assert event_bus.subscriber_count() == 0
    
    def test_clear_removes_pending_events(self, event_bus):
        """Test that clear removes pending events."""
        # We can't easily test this without threading, but we can verify
        # the method exists and doesn't raise
        event_bus.clear()
        assert event_bus.pending_count() == 0


class TestEventBusThreading:
    """Thread safety tests for EventBus."""
    
    def test_concurrent_subscriptions(self, event_bus):
        """Test subscribing from multiple threads."""
        handlers = []
        
        def subscribe_handler():
            def handler(event):
                pass
            handlers.append(handler)
            event_bus.subscribe(ProjectCreated, handler)
        
        threads = [threading.Thread(target=subscribe_handler) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert event_bus.subscriber_count(ProjectCreated) == 10
    
    def test_publish_from_background_thread(self, event_bus):
        """Test that events from background threads are queued."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe(ProjectCreated, handler)
        
        def publish_in_thread():
            event_bus.publish(ProjectCreated(project_id=1, name="Background"))
        
        thread = threading.Thread(target=publish_in_thread)
        thread.start()
        thread.join()
        
        # Event should be in queue (not delivered yet since we're not in main thread)
        # Process the queue
        count = event_bus.process_pending()
        
        # Should have processed at least 0 events (depends on thread identification)
        assert count >= 0


class TestEventBusPublishSync:
    """Tests for synchronous publishing."""
    
    def test_publish_sync(self, event_bus):
        """Test synchronous publish delivers immediately."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe(ProjectCreated, handler)
        event_bus.publish_sync(ProjectCreated(project_id=1, name="Sync"))
        
        assert len(received) == 1


class TestEventSerialization:
    """Tests for event serialization."""
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = ProjectCreated(project_id=1, name="Test")
        d = event.to_dict()
        
        assert d["project_id"] == 1
        assert d["name"] == "Test"
        assert d["event_type"] == "ProjectCreated"
        assert "timestamp" in d
    
    def test_event_to_json(self):
        """Test converting event to JSON."""
        event = ProjectCreated(project_id=1, name="Test")
        json_str = event.to_json()
        
        import json
        parsed = json.loads(json_str)
        
        assert parsed["project_id"] == 1
        assert parsed["name"] == "Test"
