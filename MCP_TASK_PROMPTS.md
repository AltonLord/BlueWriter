# BlueWriter MCP - Task Prompts

This document contains detailed prompts for each task. Each prompt is self-contained and provides enough context for implementation.

---

## Phase 1: Extract Service Layer

### Task 1.1: Create Service Base Class and Event Bus Foundation

**Goal:** Create the foundational classes for the service layer and event system.

**Context:** BlueWriter currently has business logic mixed into Qt views. We're extracting this into a clean service layer that's UI-framework agnostic.

**Files to Create:**
- `/fast/BlueWriter/services/__init__.py`
- `/fast/BlueWriter/services/base.py`
- `/fast/BlueWriter/events/__init__.py`
- `/fast/BlueWriter/events/event_bus.py`

**Requirements:**

1. `services/base.py`:
```python
class BaseService:
    def __init__(self, db_path: str, event_bus: 'EventBus'):
        self.db_path = db_path
        self.event_bus = event_bus
    
    def _get_connection(self):
        """Get a database connection for this operation."""
        # Use DatabaseManager from database/connection.py
```

2. `events/event_bus.py`:
```python
class EventBus:
    def __init__(self):
        self._subscribers = {}  # event_type -> list of callbacks
        self._queue = Queue()   # Thread-safe queue for cross-thread events
    
    def subscribe(self, event_type: type, callback: Callable) -> None:
        """Subscribe to an event type."""
        
    def unsubscribe(self, event_type: type, callback: Callable) -> None:
        """Unsubscribe from an event type."""
        
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        
    def process_pending(self) -> None:
        """Process any pending events (call from main thread)."""
```

**Reference Files:**
- `/fast/BlueWriter/database/connection.py` - DatabaseManager class
- `/fast/BlueWriter/MCP_CODING_STANDARDS.md` - Coding patterns

**Verification:**
```python
from services.base import BaseService
from events.event_bus import EventBus
eb = EventBus()
# Should import without errors
```

---

### Task 1.2: Create ProjectService

**Goal:** Extract project management logic into ProjectService.

**Context:** Currently project CRUD is in `views/project_browser.py` and `models/project.py`. We need a service that wraps these operations.

**Files to Create:**
- `/fast/BlueWriter/services/project_service.py`
- `/fast/BlueWriter/events/events.py` (add project events)

**Files to Reference:**
- `/fast/BlueWriter/models/project.py` - Project model
- `/fast/BlueWriter/views/project_browser.py` - Current project UI logic

**Requirements:**

1. Create `ProjectDTO` dataclass with fields: id, name, description, created_at, updated_at

2. Create events:
   - `ProjectCreated(project_id, name)`
   - `ProjectUpdated(project_id, fields_changed)`
   - `ProjectDeleted(project_id)`
   - `ProjectOpened(project_id)`

3. Create `ProjectService` with methods:
   - `list_projects() -> List[ProjectDTO]`
   - `get_project(project_id: int) -> ProjectDTO`
   - `create_project(name: str, description: str = "") -> ProjectDTO`
   - `update_project(project_id: int, name: str = None, description: str = None) -> ProjectDTO`
   - `delete_project(project_id: int) -> None`

4. Each method should emit appropriate events after database operations.

**Verification:**
```python
from services.project_service import ProjectService
from events.event_bus import EventBus
eb = EventBus()
ps = ProjectService("/fast/BlueWriter/data/bluewriter.db", eb)
projects = ps.list_projects()
print(f"Found {len(projects)} projects")
```

---

### Task 1.3: Create StoryService

**Goal:** Extract story management logic into StoryService.

**Files to Create:**
- `/fast/BlueWriter/services/story_service.py`
- Update `/fast/BlueWriter/events/events.py` (add story events)

**Files to Reference:**
- `/fast/BlueWriter/models/story.py` - Story model with status/publishing
- `/fast/BlueWriter/views/story_manager.py` - Current story UI logic

**Requirements:**

1. Create `StoryDTO` dataclass with fields: id, project_id, title, synopsis, sort_order, status, published_at, created_at, updated_at

2. Create events:
   - `StoryCreated(story_id, project_id, title)`
   - `StoryUpdated(story_id, fields_changed)`
   - `StoryDeleted(story_id)`
   - `StorySelected(story_id)` - When story is selected in UI
   - `StoryPublished(story_id, status)` - rough_published or final_published
   - `StoryUnpublished(story_id)`

3. Create `StoryService` with methods:
   - `list_stories(project_id: int) -> List[StoryDTO]`
   - `get_story(story_id: int) -> StoryDTO`
   - `create_story(project_id: int, title: str, synopsis: str = "") -> StoryDTO`
   - `update_story(story_id: int, title: str = None, synopsis: str = None) -> StoryDTO`
   - `delete_story(story_id: int) -> None`
   - `publish_story(story_id: int, final: bool = False) -> StoryDTO`
   - `unpublish_story(story_id: int) -> StoryDTO`
   - `reorder_stories(project_id: int, story_ids: List[int]) -> None`

4. Enforce business rules:
   - Cannot update/delete final_published stories without unpublishing first
   - Raise `RuntimeError` for locked story operations

**Verification:**
```python
from services.story_service import StoryService
from events.event_bus import EventBus
eb = EventBus()
ss = StoryService("/fast/BlueWriter/data/bluewriter.db", eb)
# Get stories for a project
stories = ss.list_stories(project_id=1)
print(f"Found {len(stories)} stories")
```

---

### Task 1.4: Create ChapterService

**Goal:** Extract chapter management logic into ChapterService.

**Files to Create:**
- `/fast/BlueWriter/services/chapter_service.py`
- Update `/fast/BlueWriter/events/events.py` (add chapter events)

**Files to Reference:**
- `/fast/BlueWriter/models/chapter.py` - Chapter model
- `/fast/BlueWriter/views/timeline_canvas.py` - Canvas/sticky note logic
- `/fast/BlueWriter/views/chapter_editor_dock.py` - Editor logic

**Requirements:**

1. Create `ChapterDTO` dataclass with fields: id, story_id, title, summary, content, board_x, board_y, color, created_at, updated_at

2. Create events:
   - `ChapterCreated(chapter_id, story_id, title, board_x, board_y)`
   - `ChapterUpdated(chapter_id, fields_changed)`
   - `ChapterDeleted(chapter_id, story_id)`
   - `ChapterMoved(chapter_id, old_x, old_y, new_x, new_y)`
   - `ChapterColorChanged(chapter_id, old_color, new_color)`
   - `ChapterOpened(chapter_id)` - Editor opened
   - `ChapterClosed(chapter_id)` - Editor closed

3. Create `ChapterService` with methods:
   - `list_chapters(story_id: int) -> List[ChapterDTO]`
   - `get_chapter(chapter_id: int) -> ChapterDTO`
   - `create_chapter(story_id: int, title: str, board_x: int, board_y: int, color: str = "#FFFF88") -> ChapterDTO`
   - `update_chapter(chapter_id: int, title: str = None, summary: str = None, content: str = None) -> ChapterDTO`
   - `delete_chapter(chapter_id: int) -> None`
   - `move_chapter(chapter_id: int, board_x: int, board_y: int) -> ChapterDTO`
   - `set_chapter_color(chapter_id: int, color: str) -> ChapterDTO`

4. Content helper methods:
   - `get_chapter_text(chapter_id: int) -> str` - Plain text extraction
   - `set_chapter_text(chapter_id: int, text: str) -> ChapterDTO` - Set as plain text
   - `get_chapter_html(chapter_id: int) -> str` - Raw HTML content
   - `set_chapter_html(chapter_id: int, html: str) -> ChapterDTO` - Set HTML
   - `insert_text(chapter_id: int, position: int, text: str) -> ChapterDTO`
   - `insert_scene_break(chapter_id: int, position: int) -> ChapterDTO`

5. Enforce business rules:
   - Check if parent story is locked before any modification
   - Validate color format (#RRGGBB)

**Verification:**
```python
from services.chapter_service import ChapterService
from events.event_bus import EventBus
eb = EventBus()
cs = ChapterService("/fast/BlueWriter/data/bluewriter.db", eb)
chapters = cs.list_chapters(story_id=1)
print(f"Found {len(chapters)} chapters")
```

---

### Task 1.5: Create EncyclopediaService

**Goal:** Extract encyclopedia management logic into EncyclopediaService.

**Files to Create:**
- `/fast/BlueWriter/services/encyclopedia_service.py`
- Update `/fast/BlueWriter/events/events.py` (add encyclopedia events)

**Files to Reference:**
- `/fast/BlueWriter/models/encyclopedia_entry.py` - Entry model
- `/fast/BlueWriter/views/encyclopedia_widget.py` - Entry list UI
- `/fast/BlueWriter/views/encyclopedia_editor_dock.py` - Editor logic

**Requirements:**

1. Create `EncyclopediaEntryDTO` with fields: id, project_id, name, category, content, tags, created_at, updated_at

2. Create events:
   - `EntryCreated(entry_id, project_id, name, category)`
   - `EntryUpdated(entry_id, fields_changed)`
   - `EntryDeleted(entry_id, project_id)`
   - `EntryOpened(entry_id)`
   - `EntryClosed(entry_id)`

3. Create `EncyclopediaService` with methods:
   - `list_entries(project_id: int, category: str = None) -> List[EncyclopediaEntryDTO]`
   - `get_entry(entry_id: int) -> EncyclopediaEntryDTO`
   - `create_entry(project_id: int, name: str, category: str, content: str = "", tags: str = "") -> EncyclopediaEntryDTO`
   - `update_entry(entry_id: int, name: str = None, category: str = None, content: str = None, tags: str = None) -> EncyclopediaEntryDTO`
   - `delete_entry(entry_id: int) -> None`
   - `search_entries(project_id: int, query: str) -> List[EncyclopediaEntryDTO]`
   - `list_categories(project_id: int) -> List[str]`

**Verification:**
```python
from services.encyclopedia_service import EncyclopediaService
from events.event_bus import EventBus
eb = EventBus()
es = EncyclopediaService("/fast/BlueWriter/data/bluewriter.db", eb)
entries = es.list_entries(project_id=1)
print(f"Found {len(entries)} entries")
```

---

### Task 1.6: Create CanvasService and EditorService

**Goal:** Create services for canvas state and editor management.

**Files to Create:**
- `/fast/BlueWriter/services/canvas_service.py`
- `/fast/BlueWriter/services/editor_service.py`
- Update `/fast/BlueWriter/events/events.py` (add canvas/editor events)

**Requirements:**

1. **CanvasService** - Manages canvas viewport state (pan/zoom)
   
   Note: This is "stateful" - it tracks the current view. The actual state will be stored in memory, not database.
   
   ```python
   @dataclass
   class CanvasViewDTO:
       pan_x: float
       pan_y: float
       zoom: float
   
   class CanvasService:
       def __init__(self, event_bus: EventBus):
           self._views = {}  # story_id -> CanvasViewDTO
       
       def get_view(self, story_id: int) -> CanvasViewDTO
       def set_pan(self, story_id: int, x: float, y: float) -> CanvasViewDTO
       def set_zoom(self, story_id: int, zoom: float) -> CanvasViewDTO
       def focus_chapter(self, story_id: int, chapter_id: int) -> CanvasViewDTO
       def fit_all(self, story_id: int) -> CanvasViewDTO
   ```

   Events:
   - `CanvasPanned(story_id, old_x, old_y, new_x, new_y)`
   - `CanvasZoomed(story_id, old_zoom, new_zoom)`

2. **EditorService** - Tracks which editors are open
   
   ```python
   @dataclass
   class OpenEditorDTO:
       editor_type: str  # "chapter" or "encyclopedia"
       item_id: int
       is_modified: bool
   
   class EditorService:
       def __init__(self, event_bus: EventBus):
           self._open_editors = {}  # editor_key -> OpenEditorDTO
       
       def list_open_editors(self) -> List[OpenEditorDTO]
       def register_editor_opened(self, editor_type: str, item_id: int) -> None
       def register_editor_closed(self, editor_type: str, item_id: int) -> None
       def set_editor_modified(self, editor_type: str, item_id: int, modified: bool) -> None
       def is_editor_open(self, editor_type: str, item_id: int) -> bool
   ```

**Verification:**
```python
from services.canvas_service import CanvasService
from services.editor_service import EditorService
from events.event_bus import EventBus
eb = EventBus()
cs = CanvasService(eb)
es = EditorService(eb)
# Should create without errors
```

---

## Phase 2: Event System

### Task 2.1: Define All Event Types

**Goal:** Create comprehensive event type definitions for all system events.

**Files to Update:**
- `/fast/BlueWriter/events/events.py`

**Requirements:**

Create a complete `events.py` with all event types organized by category:

```python
"""
BlueWriter Event Definitions

All events that can be emitted by services. Events are dataclasses
that can be serialized to JSON for logging/debugging.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import json

@dataclass
class Event:
    """Base event class with timestamp."""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['event_type'] = self.__class__.__name__
        return d
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

# Project Events
@dataclass
class ProjectCreated(Event): ...
# ... etc for all event types from Tasks 1.2-1.6
```

**Event Categories:**
1. Project events (5 types)
2. Story events (6 types)
3. Chapter events (7 types)
4. Encyclopedia events (5 types)
5. Canvas events (2 types)
6. Editor events (3 types)
7. Application events: `AppStateChanged`, `SaveRequested`, `SaveCompleted`

---

### Task 2.2: Implement Thread-Safe EventBus

**Goal:** Make EventBus fully thread-safe for cross-thread communication.

**Files to Update:**
- `/fast/BlueWriter/events/event_bus.py`

**Requirements:**

```python
import threading
from queue import Queue
from typing import Callable, Dict, List, Type
from events.events import Event

class EventBus:
    """Thread-safe event bus for publish/subscribe pattern."""
    
    def __init__(self):
        self._subscribers: Dict[Type[Event], List[Callable]] = {}
        self._lock = threading.Lock()
        self._pending_queue: Queue = Queue()
        self._main_thread_id = threading.current_thread().ident
    
    def subscribe(self, event_type: Type[Event], callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type. Thread-safe."""
        
    def unsubscribe(self, event_type: Type[Event], callback: Callable) -> None:
        """Unsubscribe from an event type. Thread-safe."""
        
    def publish(self, event: Event) -> None:
        """
        Publish an event.
        - If called from main thread: dispatch immediately
        - If called from other thread: queue for main thread processing
        """
        
    def publish_sync(self, event: Event) -> None:
        """Publish and dispatch immediately (use only from main thread)."""
        
    def process_pending(self) -> int:
        """
        Process pending events from queue. Call from main thread.
        Returns number of events processed.
        """
        
    def clear(self) -> None:
        """Clear all subscribers and pending events."""
```

**Test Requirements:**
- Test subscription/unsubscription
- Test publishing from main thread
- Test publishing from background thread
- Test process_pending drains queue correctly

---

### Task 2.3: Add Event Emission to All Services

**Goal:** Ensure all service methods emit appropriate events.

**Files to Update:**
- All service files created in Phase 1

**Requirements:**

1. Review each service method
2. Add event emission after successful database operations
3. Ensure events contain enough data for UI to update without re-fetching

Example pattern:
```python
def create_chapter(self, story_id: int, title: str, ...) -> ChapterDTO:
    # ... create in database ...
    
    # Emit event with all data UI needs
    self.event_bus.publish(ChapterCreated(
        chapter_id=chapter.id,
        story_id=story_id,
        title=title,
        board_x=board_x,
        board_y=board_y,
        color=color
    ))
    
    return chapter_dto
```

---

### Task 2.4: Create Event Logging/Debugging Utilities

**Goal:** Add tools for debugging event flow.

**Files to Create:**
- `/fast/BlueWriter/events/debug.py`

**Requirements:**

```python
class EventLogger:
    """Logs all events to console or file for debugging."""
    
    def __init__(self, event_bus: EventBus, log_file: str = None):
        self.event_bus = event_bus
        self.log_file = log_file
        self._subscribe_to_all()
    
    def _subscribe_to_all(self):
        """Subscribe to all event types."""
        
    def _log_event(self, event: Event):
        """Log event to console and/or file."""
        
class EventRecorder:
    """Records events for playback/testing."""
    
    def __init__(self, event_bus: EventBus):
        self.events: List[Event] = []
        
    def start_recording(self): ...
    def stop_recording(self): ...
    def get_events(self, event_type: Type[Event] = None) -> List[Event]: ...
    def clear(self): ...
```

---

## Phase 3: REST API

### Task 3.1: Set Up FastAPI Application Structure

**Goal:** Create the FastAPI application framework.

**Files to Create:**
- `/fast/BlueWriter/api/__init__.py`
- `/fast/BlueWriter/api/server.py`
- `/fast/BlueWriter/api/dependencies.py`
- `/fast/BlueWriter/api/routes/__init__.py`

**Requirements:**

1. `api/server.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app(services: dict) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="BlueWriter API",
        description="REST API for BlueWriter fiction writing application",
        version="1.0.0"
    )
    
    # CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store services in app state
    app.state.services = services
    
    # Register routes
    from api.routes import projects, stories, chapters, encyclopedia, canvas
    app.include_router(projects.router)
    # ... etc
    
    return app

def run_server(app: FastAPI, host: str = "127.0.0.1", port: int = 5000):
    """Run the API server (blocking)."""
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="warning")
```

2. `api/dependencies.py`:
```python
from fastapi import Request
from services.project_service import ProjectService
# ... other services

def get_project_service(request: Request) -> ProjectService:
    return request.app.state.services['project']

# ... other dependency functions
```

**Verification:**
```python
from api.server import create_app
app = create_app({})  # Empty services for now
# Should create without errors
```

---

### Task 3.2: Create Pydantic Schemas

**Goal:** Define request/response schemas for all API endpoints.

**Files to Create:**
- `/fast/BlueWriter/api/schemas.py`

**Requirements:**

Create Pydantic models for all DTOs:

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# === Project Schemas ===
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === Story Schemas ===
# ... similar pattern

# === Chapter Schemas ===
class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1)
    board_x: int = Field(default=100, ge=0)
    board_y: int = Field(default=100, ge=0)
    color: str = Field(default="#FFFF88", pattern=r"^#[0-9A-Fa-f]{6}$")

class ChapterContentUpdate(BaseModel):
    """For updating just the content."""
    content: str
    format: str = Field(default="html", pattern=r"^(html|text)$")

# ... etc for all types
```

---

### Task 3.3: Implement Project and Story Routes

**Goal:** Create REST endpoints for projects and stories.

**Files to Create:**
- `/fast/BlueWriter/api/routes/projects.py`
- `/fast/BlueWriter/api/routes/stories.py`

**Requirements:**

1. `routes/projects.py`:
```
GET    /projects           - List all projects
POST   /projects           - Create project
GET    /projects/{id}      - Get project
PUT    /projects/{id}      - Update project
DELETE /projects/{id}      - Delete project
```

2. `routes/stories.py`:
```
GET    /projects/{pid}/stories      - List stories in project
POST   /projects/{pid}/stories      - Create story in project
GET    /stories/{id}                - Get story
PUT    /stories/{id}                - Update story
DELETE /stories/{id}                - Delete story
POST   /stories/{id}/publish        - Publish story (body: {final: bool})
POST   /stories/{id}/unpublish      - Unpublish story
PUT    /projects/{pid}/stories/order - Reorder stories (body: {story_ids: [...]})
```

**Error Handling:**
- 404 for not found
- 409 for conflicts (locked story, etc.)
- 422 for validation errors (Pydantic handles automatically)

---

### Task 3.4: Implement Chapter and Encyclopedia Routes

**Goal:** Create REST endpoints for chapters and encyclopedia entries.

**Files to Create:**
- `/fast/BlueWriter/api/routes/chapters.py`
- `/fast/BlueWriter/api/routes/encyclopedia.py`

**Requirements:**

1. `routes/chapters.py`:
```
GET    /stories/{sid}/chapters      - List chapters in story
POST   /stories/{sid}/chapters      - Create chapter
GET    /chapters/{id}               - Get chapter (includes content)
PUT    /chapters/{id}               - Update chapter metadata
DELETE /chapters/{id}               - Delete chapter
PUT    /chapters/{id}/content       - Update content (body: {content, format})
PUT    /chapters/{id}/position      - Move on canvas (body: {board_x, board_y})
PUT    /chapters/{id}/color         - Change color (body: {color})
POST   /chapters/{id}/scene-break   - Insert scene break (body: {position})
GET    /chapters/{id}/text          - Get plain text only
```

2. `routes/encyclopedia.py`:
```
GET    /projects/{pid}/encyclopedia           - List entries
GET    /projects/{pid}/encyclopedia/search    - Search entries (query: q)
GET    /projects/{pid}/encyclopedia/categories - List categories
POST   /projects/{pid}/encyclopedia           - Create entry
GET    /encyclopedia/{id}                     - Get entry
PUT    /encyclopedia/{id}                     - Update entry
DELETE /encyclopedia/{id}                     - Delete entry
```

---

### Task 3.5: Implement Canvas and State Routes

**Goal:** Create REST endpoints for canvas control and app state.

**Files to Create:**
- `/fast/BlueWriter/api/routes/canvas.py`
- `/fast/BlueWriter/api/routes/state.py`

**Requirements:**

1. `routes/canvas.py`:
```
GET  /stories/{sid}/canvas         - Get canvas view state
PUT  /stories/{sid}/canvas/pan     - Set pan position (body: {x, y})
PUT  /stories/{sid}/canvas/zoom    - Set zoom level (body: {zoom})
POST /stories/{sid}/canvas/focus   - Focus on chapter (body: {chapter_id})
POST /stories/{sid}/canvas/fit     - Fit all chapters in view
GET  /stories/{sid}/canvas/layout  - Get all chapter positions
```

2. `routes/state.py`:
```
GET  /state                - Get current app state (open project, story, editors)
GET  /state/editors        - List open editors
POST /state/save-all       - Save all unsaved changes
```

---

## Phase 4: Qt Adapter Integration

### Task 4.1: Create QtEventAdapter Class

**Goal:** Create an adapter that bridges the event bus to Qt signals.

**Files to Create:**
- `/fast/BlueWriter/adapters/__init__.py`
- `/fast/BlueWriter/adapters/qt_adapter.py`

**Requirements:**

```python
from PySide6.QtCore import QObject, Signal, QMetaObject, Qt, Q_ARG
from PySide6.QtWidgets import QApplication
from events.event_bus import EventBus
from events.events import *

class QtEventAdapter(QObject):
    """
    Bridges EventBus to Qt signals.
    Ensures all Qt updates happen on main thread.
    """
    
    # Define Qt signals for each event type
    project_created = Signal(int, str)  # project_id, name
    project_updated = Signal(int, list)  # project_id, fields_changed
    project_deleted = Signal(int)
    project_opened = Signal(int)
    
    story_created = Signal(int, int, str)  # story_id, project_id, title
    story_updated = Signal(int, list)
    story_deleted = Signal(int)
    story_selected = Signal(int)
    # ... etc for all event types
    
    chapter_created = Signal(int, int, str, int, int)  # id, story_id, title, x, y
    chapter_updated = Signal(int, list)
    chapter_deleted = Signal(int, int)  # chapter_id, story_id
    chapter_moved = Signal(int, int, int, int, int)  # id, old_x, old_y, new_x, new_y
    # ... etc
    
    canvas_panned = Signal(int, float, float)  # story_id, x, y
    canvas_zoomed = Signal(int, float)  # story_id, zoom
    
    def __init__(self, event_bus: EventBus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        self._subscribe_to_events()
        
        # Timer to process pending events
        from PySide6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_events)
        self._timer.start(50)  # 50ms polling
    
    def _subscribe_to_events(self):
        """Subscribe to all event types."""
        self.event_bus.subscribe(ProjectCreated, self._on_project_created)
        self.event_bus.subscribe(ChapterCreated, self._on_chapter_created)
        # ... subscribe to all event types
    
    def _process_events(self):
        """Process pending events from background threads."""
        self.event_bus.process_pending()
    
    def _on_project_created(self, event: ProjectCreated):
        """Handle project created - emit Qt signal."""
        self.project_created.emit(event.project_id, event.name)
    
    # ... handlers for all event types that emit corresponding Qt signals
```

**Key Points:**
- All signal emissions happen on main thread (Qt requirement)
- Timer polls event_bus.process_pending() regularly
- Each Event type maps to a specific Qt signal

---

### Task 4.2: Integrate Adapter with MainWindow

**Goal:** Connect QtEventAdapter to MainWindow and wire up signal handlers.

**Files to Update:**
- `/fast/BlueWriter/views/main_window.py`

**Requirements:**

1. Import and initialize adapter in MainWindow.__init__:
```python
from adapters.qt_adapter import QtEventAdapter
from services.project_service import ProjectService
# ... other services

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize event bus and services
        self.event_bus = EventBus()
        db_path = str(get_default_db_path())
        
        self.services = {
            'project': ProjectService(db_path, self.event_bus),
            'story': StoryService(db_path, self.event_bus),
            'chapter': ChapterService(db_path, self.event_bus),
            'encyclopedia': EncyclopediaService(db_path, self.event_bus),
            'canvas': CanvasService(self.event_bus),
            'editor': EditorService(self.event_bus),
        }
        
        # Create Qt adapter
        self.event_adapter = QtEventAdapter(self.event_bus, self)
        
        # Connect signals to handlers
        self.event_adapter.chapter_created.connect(self._on_chapter_created)
        self.event_adapter.chapter_moved.connect(self._on_chapter_moved)
        # ... connect all signals
```

2. Add handler methods that update UI:
```python
def _on_chapter_created(self, chapter_id: int, story_id: int, title: str, x: int, y: int):
    """Handle chapter creation from service."""
    if self.current_story_id == story_id:
        # Refresh canvas or add sticky note directly
        self.timeline_canvas.add_sticky_note(chapter_id, title, x, y)

def _on_chapter_moved(self, chapter_id: int, old_x: int, old_y: int, new_x: int, new_y: int):
    """Handle chapter movement from service/API."""
    self.timeline_canvas.update_note_position(chapter_id, new_x, new_y)
```

---

### Task 4.3: Refactor Views to Use Services

**Goal:** Update views to call services instead of direct database access.

**Files to Update:**
- `/fast/BlueWriter/views/project_browser.py`
- `/fast/BlueWriter/views/story_manager.py`
- `/fast/BlueWriter/views/timeline_canvas.py`
- `/fast/BlueWriter/views/chapter_editor_dock.py`
- `/fast/BlueWriter/views/encyclopedia_widget.py`
- `/fast/BlueWriter/views/encyclopedia_editor_dock.py`

**Requirements:**

1. Views receive service references from MainWindow
2. Replace direct `DatabaseManager` usage with service calls
3. Remove business logic from views (move to services if not already)
4. Views should only:
   - Call service methods
   - Update their own widgets
   - Emit signals for user actions

**Example refactor in timeline_canvas.py:**

Before:
```python
def create_chapter(self, x, y):
    with DatabaseManager(get_default_db_path()) as conn:
        chapter = Chapter.create(conn, self.story_id, "New Chapter", ...)
    self.add_sticky_note(chapter)
```

After:
```python
def create_chapter(self, x, y):
    # Service handles DB and emits event
    # Event triggers _on_chapter_created which adds sticky note
    self.chapter_service.create_chapter(
        story_id=self.story_id,
        title="New Chapter",
        board_x=x,
        board_y=y
    )
```

---

### Task 4.4: Start API Server on Application Launch

**Goal:** Launch the REST API server when BlueWriter starts.

**Files to Update:**
- `/fast/BlueWriter/main.py`
- `/fast/BlueWriter/views/main_window.py`

**Requirements:**

1. Start API server in background thread on app launch:
```python
# In main.py or MainWindow.__init__
import threading
from api.server import create_app, run_server

def start_api_server(services: dict, port: int = 5000):
    """Start API server in background thread."""
    app = create_app(services)
    thread = threading.Thread(
        target=run_server,
        args=(app, "127.0.0.1", port),
        daemon=True  # Dies when main app exits
    )
    thread.start()
    return thread
```

2. Add server start to MainWindow initialization:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        # ... existing init ...
        
        # Start API server
        self.api_thread = start_api_server(self.services, port=5000)
        print("BlueWriter API running on http://127.0.0.1:5000")
```

3. Add shutdown handling in closeEvent:
```python
def closeEvent(self, event):
    # API thread is daemon, will die automatically
    # But we should save any pending work
    self.services['editor'].save_all_modified()
    super().closeEvent(event)
```

**Verification:**
- Start BlueWriter
- Open browser to http://127.0.0.1:5000/docs
- Should see Swagger UI with all endpoints

---

## Phase 5: MCP Server

### Task 5.1: Set Up MCP Server Structure

**Goal:** Create the MCP server application framework.

**Files to Create:**
- `/fast/BlueWriter/mcp/__init__.py`
- `/fast/BlueWriter/mcp/server.py`
- `/fast/BlueWriter/mcp/tools/__init__.py`

**Requirements:**

1. `mcp/server.py`:
```python
"""
BlueWriter MCP Server

Provides AI assistants with tools to control BlueWriter.
Communicates with BlueWriter via REST API on localhost:5000.
"""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server

API_BASE = "http://127.0.0.1:5000"

async def main():
    """Main entry point for MCP server."""
    server = Server("bluewriter")
    
    # Register all tools
    from mcp.tools import (
        project_tools,
        story_tools,
        chapter_tools,
        encyclopedia_tools,
        canvas_tools
    )
    
    await project_tools.register(server, API_BASE)
    await story_tools.register(server, API_BASE)
    await chapter_tools.register(server, API_BASE)
    await encyclopedia_tools.register(server, API_BASE)
    await canvas_tools.register(server, API_BASE)
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
```

2. Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "bluewriter": {
      "command": "python",
      "args": ["/fast/BlueWriter/mcp/server.py"]
    }
  }
}
```

---

### Task 5.2: Implement Project and Story Tools

**Goal:** Create MCP tools for project and story management.

**Files to Create:**
- `/fast/BlueWriter/mcp/tools/project_tools.py`
- `/fast/BlueWriter/mcp/tools/story_tools.py`

**Requirements:**

1. `project_tools.py`:
```python
import httpx
from mcp.server import Server

async def register(server: Server, api_base: str):
    """Register project-related MCP tools."""
    
    @server.tool()
    async def list_projects() -> str:
        """List all BlueWriter projects.
        
        Returns a JSON array of projects with id, name, description.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base}/projects")
            return response.text
    
    @server.tool()
    async def create_project(name: str, description: str = "") -> str:
        """Create a new BlueWriter project.
        
        Args:
            name: Project name (required)
            description: Optional project description
            
        Returns:
            JSON object with created project details
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base}/projects",
                json={"name": name, "description": description}
            )
            return response.text
    
    # ... get_project, update_project, delete_project, open_project
```

2. `story_tools.py` - similar pattern for all story operations

**Tool Documentation:**
- Each tool must have a clear docstring - this becomes the tool description for Claude
- Args section documents parameters
- Returns section explains what Claude will receive

---

### Task 5.3: Implement Chapter Tools

**Goal:** Create MCP tools for chapter management.

**Files to Create:**
- `/fast/BlueWriter/mcp/tools/chapter_tools.py`

**Requirements:**

```python
async def register(server: Server, api_base: str):
    
    @server.tool()
    async def list_chapters(story_id: int) -> str:
        """List all chapters in a story.
        
        Args:
            story_id: ID of the story
            
        Returns:
            JSON array of chapters with id, title, summary, position
        """
    
    @server.tool()
    async def create_chapter(
        story_id: int,
        title: str,
        board_x: int = 100,
        board_y: int = 100,
        color: str = "#FFFF88"
    ) -> str:
        """Create a new chapter in a story.
        
        Args:
            story_id: ID of the story to add chapter to
            title: Chapter title
            board_x: X position on canvas (default 100)
            board_y: Y position on canvas (default 100)
            color: Sticky note color as hex (default yellow)
            
        Returns:
            JSON object with created chapter details
        """
    
    @server.tool()
    async def get_chapter(chapter_id: int) -> str:
        """Get chapter details including content.
        
        Args:
            chapter_id: ID of the chapter
            
        Returns:
            JSON object with full chapter details and content
        """
    
    @server.tool()
    async def move_chapter(chapter_id: int, x: int, y: int) -> str:
        """Move a chapter's sticky note on the canvas.
        
        Args:
            chapter_id: ID of the chapter to move
            x: New X position
            y: New Y position
            
        Returns:
            JSON object with updated chapter position
        """
    
    @server.tool()
    async def open_chapter(chapter_id: int) -> str:
        """Open a chapter in the editor.
        
        This will open the chapter editor dock in BlueWriter's UI.
        
        Args:
            chapter_id: ID of the chapter to open
            
        Returns:
            Confirmation message
        """
    
    # ... delete_chapter, set_chapter_color, close_chapter
```

---

### Task 5.4: Implement Chapter Content Tools

**Goal:** Create MCP tools for editing chapter content.

**Files to Update:**
- `/fast/BlueWriter/mcp/tools/chapter_tools.py`

**Requirements:**

```python
    @server.tool()
    async def get_chapter_text(chapter_id: int) -> str:
        """Get chapter content as plain text.
        
        Useful for reading/analyzing content without HTML markup.
        
        Args:
            chapter_id: ID of the chapter
            
        Returns:
            Plain text content of the chapter
        """
    
    @server.tool()
    async def set_chapter_content(
        chapter_id: int,
        content: str,
        format: str = "text"
    ) -> str:
        """Set chapter content.
        
        Args:
            chapter_id: ID of the chapter
            content: New content to set
            format: Either "text" (plain text) or "html" (rich text)
            
        Returns:
            Confirmation with updated chapter info
        """
    
    @server.tool()
    async def append_to_chapter(chapter_id: int, text: str) -> str:
        """Append text to the end of a chapter.
        
        Args:
            chapter_id: ID of the chapter
            text: Text to append
            
        Returns:
            Updated chapter info
        """
    
    @server.tool()
    async def insert_scene_break(chapter_id: int) -> str:
        """Insert a scene break (***) at the end of the chapter.
        
        Args:
            chapter_id: ID of the chapter
            
        Returns:
            Confirmation message
        """
    
    @server.tool()
    async def find_in_chapter(chapter_id: int, query: str) -> str:
        """Find text occurrences in a chapter.
        
        Args:
            chapter_id: ID of the chapter
            query: Text to search for
            
        Returns:
            JSON array of matches with positions
        """
    
    @server.tool()
    async def replace_in_chapter(
        chapter_id: int,
        find: str,
        replace: str,
        all_occurrences: bool = True
    ) -> str:
        """Find and replace text in a chapter.
        
        Args:
            chapter_id: ID of the chapter
            find: Text to find
            replace: Text to replace with
            all_occurrences: Replace all (True) or just first (False)
            
        Returns:
            Number of replacements made
        """
```

---

### Task 5.5: Implement Encyclopedia Tools

**Goal:** Create MCP tools for encyclopedia management.

**Files to Create:**
- `/fast/BlueWriter/mcp/tools/encyclopedia_tools.py`

**Requirements:**

```python
async def register(server: Server, api_base: str):
    
    @server.tool()
    async def list_encyclopedia_entries(
        project_id: int,
        category: str = None
    ) -> str:
        """List encyclopedia entries in a project.
        
        Args:
            project_id: ID of the project
            category: Optional category filter
            
        Returns:
            JSON array of entries with id, name, category, tags
        """
    
    @server.tool()
    async def search_encyclopedia(project_id: int, query: str) -> str:
        """Search encyclopedia entries by keyword.
        
        Searches name, content, and tags.
        
        Args:
            project_id: ID of the project
            query: Search keyword
            
        Returns:
            JSON array of matching entries
        """
    
    @server.tool()
    async def create_encyclopedia_entry(
        project_id: int,
        name: str,
        category: str,
        content: str = "",
        tags: str = ""
    ) -> str:
        """Create a new encyclopedia entry.
        
        Args:
            project_id: ID of the project
            name: Entry name (e.g., character name, location name)
            category: Category (Character, Location, Item, Event, etc.)
            content: Entry content/description
            tags: Comma-separated tags
            
        Returns:
            JSON object with created entry details
        """
    
    @server.tool()
    async def update_encyclopedia_entry(
        entry_id: int,
        name: str = None,
        category: str = None,
        content: str = None,
        tags: str = None
    ) -> str:
        """Update an encyclopedia entry.
        
        Only provide fields you want to change.
        
        Args:
            entry_id: ID of the entry to update
            name: New name (optional)
            category: New category (optional)
            content: New content (optional)
            tags: New tags (optional)
            
        Returns:
            JSON object with updated entry
        """
    
    @server.tool()
    async def list_categories(project_id: int) -> str:
        """List all encyclopedia categories in use.
        
        Args:
            project_id: ID of the project
            
        Returns:
            JSON array of category names
        """
    
    # ... get_entry, delete_entry
```

---

### Task 5.6: Implement Canvas and UI State Tools

**Goal:** Create MCP tools for canvas control and app state.

**Files to Create:**
- `/fast/BlueWriter/mcp/tools/canvas_tools.py`

**Requirements:**

```python
async def register(server: Server, api_base: str):
    
    @server.tool()
    async def get_canvas_view(story_id: int) -> str:
        """Get current canvas pan and zoom state.
        
        Args:
            story_id: ID of the story
            
        Returns:
            JSON object with pan_x, pan_y, zoom
        """
    
    @server.tool()
    async def pan_canvas(story_id: int, x: float, y: float) -> str:
        """Pan the canvas to specific coordinates.
        
        Args:
            story_id: ID of the story
            x: X coordinate to pan to
            y: Y coordinate to pan to
            
        Returns:
            Updated canvas view state
        """
    
    @server.tool()
    async def zoom_canvas(story_id: int, zoom: float) -> str:
        """Set canvas zoom level.
        
        Args:
            story_id: ID of the story
            zoom: Zoom level (0.1 to 3.0, where 1.0 is 100%)
            
        Returns:
            Updated canvas view state
        """
    
    @server.tool()
    async def focus_chapter(story_id: int, chapter_id: int) -> str:
        """Pan and zoom to center a specific chapter.
        
        Args:
            story_id: ID of the story
            chapter_id: ID of the chapter to focus on
            
        Returns:
            Updated canvas view state
        """
    
    @server.tool()
    async def get_app_state() -> str:
        """Get current BlueWriter application state.
        
        Returns:
            JSON object with:
            - current_project_id (or null)
            - current_story_id (or null)  
            - open_editors: list of {type, item_id, is_modified}
        """
    
    @server.tool()
    async def save_all() -> str:
        """Save all unsaved changes in open editors.
        
        Returns:
            Confirmation with number of items saved
        """
```

---

## Phase 6: Testing & Documentation

### Task 6.1: Service Unit Tests

**Goal:** Create unit tests for all services.

**Files to Create:**
- `/fast/BlueWriter/tests/test_services/`
- `/fast/BlueWriter/tests/test_services/test_project_service.py`
- etc.

**Requirements:**
- Test each service method
- Use test database fixture
- Verify event emission

---

### Task 6.2: API Integration Tests

**Goal:** Create integration tests for REST API.

**Files to Create:**
- `/fast/BlueWriter/tests/test_api/`

**Requirements:**
- Use FastAPI TestClient
- Test each endpoint
- Test error cases

---

### Task 6.3: MCP Tool Tests

**Goal:** Create end-to-end tests for MCP tools.

**Files to Create:**
- `/fast/BlueWriter/tests/test_mcp/`

**Requirements:**
- Mock API responses
- Test tool registration
- Test error handling

---

### Task 6.4: Generate Documentation

**Goal:** Create comprehensive documentation.

**Files to Create:**
- `/fast/BlueWriter/docs/API.md` - REST API documentation
- `/fast/BlueWriter/docs/MCP_TOOLS.md` - MCP tool reference
- Update README.md with MCP instructions

**Requirements:**
- Export OpenAPI spec from FastAPI
- Document all MCP tools with examples
- Add troubleshooting section
