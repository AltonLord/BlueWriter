# BlueWriter MCP - Coding Standards

## General Principles

1. **Service Layer is UI-Free** - Services must NEVER import Qt or any UI framework
2. **Type Everything** - Use type hints on all function signatures
3. **Dataclasses for DTOs** - Use dataclasses for data transfer, not raw dicts
4. **Explicit Over Implicit** - Prefer explicit IDs over "current" state magic
5. **Fail Fast** - Validate inputs early, raise clear exceptions

## File Organization

### Services (`/services/`)
```python
"""
Service module docstring explaining purpose.
"""
from dataclasses import dataclass
from typing import List, Optional
from services.base import BaseService
from events.event_bus import EventBus
from events.events import ChapterCreated, ChapterUpdated

@dataclass
class ChapterDTO:
    """Data transfer object for chapters."""
    id: int
    story_id: int
    title: str
    summary: Optional[str]
    content: str
    board_x: int
    board_y: int
    color: str

class ChapterService(BaseService):
    """Handles all chapter-related operations."""
    
    def __init__(self, db_path: str, event_bus: EventBus):
        super().__init__(db_path, event_bus)
    
    def get_chapter(self, chapter_id: int) -> ChapterDTO:
        """Get chapter by ID.
        
        Args:
            chapter_id: The chapter's database ID
            
        Returns:
            ChapterDTO with chapter data
            
        Raises:
            ValueError: If chapter not found
        """
        # Implementation
```

### Events (`/events/`)
```python
"""Event definitions for the event bus."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Event:
    """Base event class."""
    timestamp: datetime
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ChapterCreated(Event):
    """Emitted when a chapter is created."""
    chapter_id: int
    story_id: int
    title: str
    board_x: int
    board_y: int

@dataclass  
class ChapterUpdated(Event):
    """Emitted when a chapter is modified."""
    chapter_id: int
    fields_changed: List[str]
```

### API Routes (`/api/routes/`)
```python
"""Chapter API routes."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from api.schemas import ChapterResponse, ChapterCreate, ChapterUpdate
from services.chapter_service import ChapterService

router = APIRouter(prefix="/chapters", tags=["chapters"])

@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(chapter_id: int, service: ChapterService = Depends(get_chapter_service)):
    """Get a chapter by ID."""
    try:
        return service.get_chapter(chapter_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### MCP Tools (`/mcp/tools/`)
```python
"""Chapter MCP tools."""
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

async def register_chapter_tools(server: Server, api_base: str):
    """Register all chapter-related MCP tools."""
    
    @server.tool()
    async def get_chapter(chapter_id: int) -> str:
        """Get chapter details by ID.
        
        Args:
            chapter_id: The chapter's database ID
            
        Returns:
            JSON string with chapter details
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base}/chapters/{chapter_id}")
            response.raise_for_status()
            return response.text
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Services | `XxxService` | `ChapterService` |
| DTOs | `XxxDTO` | `ChapterDTO` |
| Events | Past tense verb | `ChapterCreated`, `CanvasPanned` |
| API Schemas | `XxxResponse`, `XxxCreate`, `XxxUpdate` | `ChapterResponse` |
| MCP Tools | `snake_case` verb_noun | `get_chapter`, `create_story` |

## Error Handling

### Services
```python
# Raise ValueError for "not found"
raise ValueError(f"Chapter {chapter_id} not found")

# Raise TypeError for invalid input types
raise TypeError(f"Expected int, got {type(chapter_id)}")

# Raise RuntimeError for state errors
raise RuntimeError("Cannot edit locked story")
```

### API
```python
# Map service exceptions to HTTP codes
try:
    result = service.method()
except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
except RuntimeError as e:
    raise HTTPException(status_code=409, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal error")
```

### MCP Tools
```python
# Return error messages as content, don't raise
try:
    result = await client.get(url)
    return result.text
except httpx.HTTPStatusError as e:
    return f"Error: {e.response.status_code} - {e.response.text}"
except Exception as e:
    return f"Error: {str(e)}"
```

## Threading Rules

1. **Services are thread-safe** - Use connection per call, not shared
2. **EventBus uses queues** - Thread-safe publish, main thread consume
3. **Qt Adapter on main thread** - All widget updates via QMetaObject.invokeMethod
4. **API runs in background** - uvicorn in daemon thread

## Testing Requirements

1. Each service needs unit tests
2. Each API route needs integration tests
3. MCP tools need end-to-end tests
4. Use pytest fixtures for database setup

## Documentation Requirements

1. Module docstring at top of each file
2. Class docstring explaining purpose
3. Method docstrings with Args/Returns/Raises
4. Type hints on all public methods
5. Comments for non-obvious logic

## Imports Order

```python
# Standard library
import json
from datetime import datetime
from typing import List, Optional

# Third party
from fastapi import APIRouter
from pydantic import BaseModel

# Local - events first
from events.event_bus import EventBus
from events.events import ChapterCreated

# Local - services
from services.base import BaseService

# Local - models (database)
from models.chapter import Chapter

# Local - other
from database.connection import DatabaseManager
```
