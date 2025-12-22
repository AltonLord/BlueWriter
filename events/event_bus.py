"""
Event bus for BlueWriter.

Provides a simple publish/subscribe mechanism for decoupling
services from UI components. Events are published by services
and consumed by UI adapters.

This is the simple, single-threaded version. Thread-safe
queuing will be added in Task 2.2.
"""
from queue import Queue
from typing import Callable, Dict, List, Type

from events import Event


class EventBus:
    """Simple publish/subscribe event bus.
    
    Services publish events after state changes. UI adapters
    subscribe to events and update widgets accordingly.
    
    Example:
        bus = EventBus()
        
        # Subscribe to events
        def on_chapter_created(event):
            print(f"Chapter created: {event.chapter_id}")
        
        bus.subscribe(ChapterCreated, on_chapter_created)
        
        # Publish events
        bus.publish(ChapterCreated(chapter_id=1, story_id=1, title="Ch 1"))
    """
    
    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: Dict[Type[Event], List[Callable[[Event], None]]] = {}
        self._queue: Queue = Queue()
    
    def subscribe(self, event_type: Type[Event], callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type.
        
        Args:
            event_type: The event class to subscribe to
            callback: Function to call when event is published.
                      Receives the event instance as its only argument.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: Type[Event], callback: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type.
        
        Args:
            event_type: The event class to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass  # Callback wasn't subscribed
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.
        
        Currently dispatches immediately. Thread-safe queuing
        will be added in Task 2.2.
        
        Args:
            event: The event instance to publish
        """
        event_type = type(event)
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    # Log but don't crash - other subscribers should still run
                    print(f"Error in event handler for {event_type.__name__}: {e}")
    
    def process_pending(self) -> int:
        """Process any pending events from the queue.
        
        This is a placeholder for the thread-safe version in Task 2.2.
        Currently returns 0 since events are dispatched immediately.
        
        Returns:
            Number of events processed (always 0 in this version)
        """
        # Will be implemented properly in Task 2.2
        return 0
    
    def clear(self) -> None:
        """Clear all subscribers and pending events.
        
        Useful for testing or resetting state.
        """
        self._subscribers.clear()
        # Clear the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Exception:
                break


__all__ = ['EventBus']
