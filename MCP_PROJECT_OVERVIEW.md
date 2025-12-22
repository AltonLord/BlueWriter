# BlueWriter MCP Integration Project

## Overview

This project adds Model Context Protocol (MCP) support to BlueWriter, enabling AI assistants to control the application programmatically. The architecture is designed to be **UI-framework agnostic**, allowing future migration from Qt to other frameworks (mobile, web, etc.).

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Server                                │
│              (bluewriter-mcp - separate process)                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP/REST (localhost:5000)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BlueWriter Application                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                 REST API Layer (FastAPI)                     ││
│  │            Runs in background thread on app start            ││
│  └─────────────────────┬───────────────────────────────────────┘│
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────────┐│
│  │                    Service Layer                             ││
│  │         (Pure Python - NO Qt/UI dependencies)                ││
│  │  ProjectService, StoryService, ChapterService,               ││
│  │  EncyclopediaService, CanvasService, EditorService           ││
│  └─────────────────────┬───────────────────────────────────────┘│
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────────┐│
│  │                    Event Bus                                 ││
│  │         (Framework-agnostic pub/sub system)                  ││
│  │  Events: chapter_created, chapter_updated, canvas_panned,   ││
│  │          story_selected, encyclopedia_updated, etc.          ││
│  └─────────────────────┬───────────────────────────────────────┘│
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────────┐│
│  │                 Qt UI Adapter                                ││
│  │    Subscribes to events, updates Qt widgets on main thread   ││
│  └─────────────────────┬───────────────────────────────────────┘│
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────────┐│
│  │              Qt UI (MainWindow, Editors, Canvas)             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Service Layer is Source of Truth** - All business logic lives here, not in UI
2. **REST API is the Contract** - MCP talks to REST, not database directly
3. **Events are Abstract** - UI subscribes to events, any framework can implement
4. **UI Adapter Handles Threading** - REST runs in background, adapter ensures thread safety
5. **Stateless API with Convenience** - API uses explicit IDs, MCP tools can track "current" state

## Project Phases

| Phase | Description | Estimated Tasks |
|-------|-------------|-----------------|
| **Phase 1** | Extract Service Layer | 6 tasks |
| **Phase 2** | Event System | 4 tasks |
| **Phase 3** | REST API | 5 tasks |
| **Phase 4** | Qt Adapter Integration | 4 tasks |
| **Phase 5** | MCP Server | 6 tasks |
| **Phase 6** | Testing & Documentation | 4 tasks |

## File Structure (Target)

```
/fast/BlueWriter/
├── services/                    # NEW - Service layer
│   ├── __init__.py
│   ├── base.py                  # Base service class
│   ├── project_service.py
│   ├── story_service.py
│   ├── chapter_service.py
│   ├── encyclopedia_service.py
│   ├── canvas_service.py
│   └── editor_service.py
├── events/                      # NEW - Event system
│   ├── __init__.py
│   ├── event_bus.py             # Framework-agnostic event bus
│   └── events.py                # Event type definitions
├── api/                         # NEW - REST API
│   ├── __init__.py
│   ├── server.py                # FastAPI app setup
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── projects.py
│   │   ├── stories.py
│   │   ├── chapters.py
│   │   ├── encyclopedia.py
│   │   └── canvas.py
│   └── schemas.py               # Pydantic models
├── adapters/                    # NEW - UI adapters
│   ├── __init__.py
│   └── qt_adapter.py            # Qt-specific event handling
├── mcp/                         # NEW - MCP server (separate process)
│   ├── __init__.py
│   ├── server.py                # MCP server implementation
│   └── tools/
│       ├── __init__.py
│       ├── project_tools.py
│       ├── story_tools.py
│       ├── chapter_tools.py
│       ├── encyclopedia_tools.py
│       └── canvas_tools.py
├── models/                      # EXISTING - Data models
├── views/                       # EXISTING - Qt UI (will be refactored)
├── database/                    # EXISTING - Database layer
└── utils/                       # EXISTING - Utilities
```

## MCP Tools Inventory

### Project Tools
| Tool | Description |
|------|-------------|
| `list_projects` | List all projects |
| `get_project` | Get project details |
| `create_project` | Create new project |
| `update_project` | Update project name/description |
| `delete_project` | Delete project |
| `open_project` | Open project in UI |

### Story Tools
| Tool | Description |
|------|-------------|
| `list_stories` | List stories in project |
| `get_story` | Get story details |
| `create_story` | Create new story |
| `update_story` | Update story title/synopsis |
| `delete_story` | Delete story |
| `select_story` | Select story in UI |
| `get_story_status` | Get publish status |
| `publish_story` | Publish story (rough/final) |
| `unpublish_story` | Unpublish story |

### Chapter Tools
| Tool | Description |
|------|-------------|
| `list_chapters` | List chapters in story |
| `get_chapter` | Get chapter with content |
| `create_chapter` | Create new chapter |
| `update_chapter` | Update title/summary/content |
| `delete_chapter` | Delete chapter |
| `open_chapter` | Open chapter in editor |
| `close_chapter` | Close chapter editor |
| `move_chapter` | Move sticky note on canvas |
| `set_chapter_color` | Change sticky note color |

### Chapter Content Tools
| Tool | Description |
|------|-------------|
| `get_chapter_text` | Get plain text content |
| `set_chapter_text` | Set content (plain text) |
| `get_chapter_html` | Get rich text (HTML) |
| `set_chapter_html` | Set content (HTML) |
| `insert_text` | Insert text at position |
| `apply_formatting` | Apply bold/italic/etc to range |
| `insert_scene_break` | Insert scene divider |
| `find_in_chapter` | Find text, return positions |
| `replace_in_chapter` | Find and replace text |

### Encyclopedia Tools
| Tool | Description |
|------|-------------|
| `list_encyclopedia_entries` | List entries (optional category filter) |
| `get_encyclopedia_entry` | Get entry details |
| `create_encyclopedia_entry` | Create new entry |
| `update_encyclopedia_entry` | Update name/category/tags/content |
| `delete_encyclopedia_entry` | Delete entry |
| `search_encyclopedia` | Search entries by keyword |
| `list_categories` | List all categories in use |

### Canvas Tools
| Tool | Description |
|------|-------------|
| `get_canvas_view` | Get current pan/zoom state |
| `pan_canvas` | Pan to coordinates |
| `zoom_canvas` | Set zoom level |
| `focus_chapter` | Pan/zoom to show specific chapter |
| `fit_all_chapters` | Zoom to fit all chapters |
| `get_canvas_layout` | Get all chapter positions |

### UI State Tools
| Tool | Description |
|------|-------------|
| `get_app_state` | Get current project/story/editors open |
| `get_open_editors` | List open chapter editors |
| `save_all` | Save all unsaved changes |

## Dependencies (New)

```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
mcp>=1.0.0
```

## Current State

See `MCP_PROJECT_STATE.md` for current progress tracking.

## Getting Started

1. Read this overview document
2. Check `MCP_PROJECT_STATE.md` for current phase/task
3. Read the specific task prompt
4. Implement following the coding standards in `MCP_CODING_STANDARDS.md`
5. Test the implementation
6. Update state document
7. Commit changes

## Reference Files

- `MCP_PROJECT_STATE.md` - Current progress and state
- `MCP_CODING_STANDARDS.md` - Code style and patterns
- `MCP_TASK_PROMPTS.md` - Detailed prompts for each task
- `MCP_API_SPEC.md` - REST API specification (created in Phase 3)
