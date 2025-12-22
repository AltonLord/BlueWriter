"""
Event bus for BlueWriter.

Provides a thread-safe publish/subscribe mechanism for decoupling
services from UI components. Events are published by services
and consumed by UI adapters.

Thread Safety:
- Subscriber list modifications are protected by a lock
- Events published from non-main threads are queued
- Queue is processed on main thread via process_pending()
"""
import threading
from queue import Queue, Empty
from typing import Callable, Dict, List, Type

from events import Event


class EventBus:
    """Thread-safe publish/subscribe event bus.
    
    Services publish events after state changes. UI adapters
    subscribe to events and update widgets accordingly.
    
    Thread Safety:
    - Events published from main thread dispatch immediately
    - Events published from background threads are queued
    - Call process_pending() from main thread to dispatch queued events
    
    Example:
        bus = EventBus()
        
        # Subscribe to events
        def on_chapter_created(event):
            print(f"Chapter created: {event.chapter_id}")
        
        bus.subscribe(ChapterCreated, on_chapter_created)
        
        # Publish events (thread-safe)
        bus.publish(ChapterCreated(chapter_id=1, story_id=1, title="Ch 1"))
        
        # Process queued events from main thread
        bus.process_pending()
    """
    
    def __init__(self) -> None:
        """Initialize the event bus."""
        self._subscribers: Dict[Type[Event], List[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()
        self._pending_queue: Queue = Queue()
        self._main_thread_id = threading.current_thread().ident
    
    def _is_main_thread(self) -> bool:
        """Check if current thread is the main thread."""
        return threading.current_thread().ident == self._main_thread_id
    
    def subscribe(self, event_type: Type[Event], callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type. Thread-safe.
        
        Args:
            event_type: The event class to subscribe to
            callback: Function to call when event is published.
                      Receives the event instance as its only argument.
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: Type[Event], callback: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type. Thread-safe.
        
        Args:
            event_type: The event class to unsubscribe from
            callback: The callback function to remove
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass  # Callback wasn't subscribed
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.
        
        Thread-safe behavior:
        - From main thread: dispatches immediately
        - From other threads: queues for main thread processing
        
        Args:
            event: The event instance to publish
        """
        if self._is_main_thread():
            self._dispatch(event)
        else:
            # Queue for main thread processing
            self._pending_queue.put(event)
    
    def publish_sync(self, event: Event) -> None:
        """Publish and dispatch immediately. Use only from main thread.
        
        Warning: Calling from background thread may cause Qt issues
        since callbacks may update UI widgets.
        
        Args:
            event: The event instance to publish
        """
        self._dispatch(event)
    
    def _dispatch(self, event: Event) -> None:
        """Dispatch an event to all subscribers.
        
        Internal method - handles actual callback invocation.
        
        Args:
            event: The event instance to dispatch
        """
        event_type = type(event)
        
        # Get subscribers with lock held (copy to avoid holding lock during callbacks)
        with self._lock:
            callbacks = list(self._subscribers.get(event_type, []))
        
        # Dispatch without lock (callbacks may take time)
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                # Log but don't crash - other subscribers should still run
                print(f"Error in event handler for {event_type.__name__}: {e}")
    
    def process_pending(self) -> int:
        """Process pending events from the queue.
        
        Call this from the main thread (e.g., via QTimer) to
        dispatch events that were published from background threads.
        
        Returns:
            Number of events processed
        """
        count = 0
        while True:
            try:
                event = self._pending_queue.get_nowait()
                self._dispatch(event)
                count += 1
            except Empty:
                break
        return count
    
    def pending_count(self) -> int:
        """Get the number of pending events in the queue.
        
        Returns:
            Number of events waiting to be processed
        """
        return self._pending_queue.qsize()
    
    def subscriber_count(self, event_type: Type[Event] = None) -> int:
        """Get the number of subscribers.
        
        Args:
            event_type: If provided, count for this type only.
                        If None, count total across all types.
        
        Returns:
            Number of subscribers
        """
        with self._lock:
            if event_type is not None:
                return len(self._subscribers.get(event_type, []))
            return sum(len(callbacks) for callbacks in self._subscribers.values())
    
    def clear(self) -> None:
        """Clear all subscribers and pending events.
        
        Useful for testing or resetting state.
        """
        with self._lock:
            self._subscribers.clear()
        
        # Clear the queue
        while True:
            try:
                self._pending_queue.get_nowait()
            except Empty:
                break


__all__ = ['EventBus']
