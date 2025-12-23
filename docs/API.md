# BlueWriter REST API Documentation

BlueWriter exposes a REST API on `http://127.0.0.1:5000` when the application is running. This API enables programmatic control of the writing application.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health](#health)
  - [Projects](#projects)
  - [Stories](#stories)
  - [Chapters](#chapters)
  - [Encyclopedia](#encyclopedia)
  - [Canvas](#canvas)
  - [State](#state)
- [Error Handling](#error-handling)
- [OpenAPI Specification](#openapi-specification)

---

## Overview

| Property | Value |
|----------|-------|
| Base URL | `http://127.0.0.1:5000` |
| Format | JSON |
| Methods | GET, POST, PUT, DELETE |

The API starts automatically when BlueWriter launches. All responses are JSON-formatted.

---

## Authentication

Currently, the API does not require authentication as it only binds to localhost. This may change in future versions.

---

## Endpoints

### Health

#### `GET /`
Root endpoint - returns API information.

**Response:**
```json
{
  "name": "BlueWriter API",
  "version": "1.0.0",
  "status": "running"
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000000"
}
```

---

### Projects

#### `GET /projects`
List all projects.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "My Novel",
    "description": "A science fiction epic",
    "created_at": "2025-01-10T08:00:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

#### `POST /projects`
Create a new project.

**Request Body:**
```json
{
  "name": "New Project",
  "description": "Optional description"
}
```

**Response:** `201 Created`
```json
{
  "id": 2,
  "name": "New Project",
  "description": "Optional description",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

#### `GET /projects/{project_id}`
Get a specific project.

**Response:** `200 OK` or `404 Not Found`

#### `PUT /projects/{project_id}`
Update a project.

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response:** `200 OK`

#### `DELETE /projects/{project_id}`
Delete a project and all its contents.

**Response:** `200 OK`
```json
{
  "message": "Project deleted",
  "id": 1
}
```

#### `POST /projects/{project_id}/open`
Open/select a project in the UI.

**Response:** `200 OK`
```json
{
  "message": "Project opened",
  "project_id": 1
}
```

---

### Stories

#### `GET /projects/{project_id}/stories`
List all stories in a project.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "project_id": 1,
    "title": "Book One",
    "synopsis": "The beginning",
    "sort_order": 0,
    "status": "draft",
    "is_locked": false,
    "is_published": false,
    "created_at": "2025-01-10T08:00:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

**Status Values:** `draft`, `rough_published`, `final_published`

#### `POST /projects/{project_id}/stories`
Create a new story.

**Request Body:**
```json
{
  "title": "New Story",
  "synopsis": "Optional synopsis"
}
```

**Response:** `201 Created`

#### `GET /stories/{story_id}`
Get a specific story.

#### `PUT /stories/{story_id}`
Update a story.

**Request Body:**
```json
{
  "title": "Updated Title",
  "synopsis": "Updated synopsis"
}
```

**Note:** Cannot update `final_published` stories. Returns `409 Conflict`.

#### `DELETE /stories/{story_id}`
Delete a story and all its chapters.

**Note:** Cannot delete `final_published` stories.

#### `POST /stories/{story_id}/select`
Select a story in the UI (displays on canvas).

#### `POST /stories/{story_id}/publish`
Publish a story.

**Request Body:**
```json
{
  "final": false
}
```

- `final: false` → `rough_published` (still editable)
- `final: true` → `final_published` (locked)

#### `POST /stories/{story_id}/unpublish`
Unpublish a story (reverts to draft, unlocks).

#### `PUT /projects/{project_id}/stories/order`
Reorder stories.

**Request Body:**
```json
{
  "story_ids": [3, 1, 2]
}
```

---

### Chapters

#### `GET /stories/{story_id}/chapters`
List all chapters in a story.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "story_id": 1,
    "title": "Chapter One",
    "summary": "Introduction",
    "board_x": 100,
    "board_y": 100,
    "color": "#FFFF88",
    "created_at": "2025-01-10T08:00:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

#### `POST /stories/{story_id}/chapters`
Create a new chapter.

**Request Body:**
```json
{
  "title": "New Chapter",
  "board_x": 200,
  "board_y": 150,
  "color": "#FFFF88"
}
```

**Defaults:**
- `board_x`: 100
- `board_y`: 100  
- `color`: "#FFFF88" (yellow)

#### `GET /chapters/{chapter_id}`
Get a chapter including its content.

**Response includes:**
```json
{
  "id": 1,
  "title": "Chapter One",
  "summary": "Introduction",
  "content": "<p>Chapter content in HTML...</p>",
  "board_x": 100,
  "board_y": 100,
  "color": "#FFFF88"
}
```

#### `PUT /chapters/{chapter_id}`
Update chapter metadata.

**Request Body:**
```json
{
  "title": "Updated Title",
  "summary": "Updated summary"
}
```

#### `DELETE /chapters/{chapter_id}`
Delete a chapter.

#### `PUT /chapters/{chapter_id}/position`
Move a chapter on the canvas.

**Request Body:**
```json
{
  "board_x": 500,
  "board_y": 300
}
```

**Note:** Negative coordinates are allowed.

#### `PUT /chapters/{chapter_id}/color`
Change chapter sticky note color.

**Request Body:**
```json
{
  "color": "#FF8888"
}
```

**Color format:** `#RRGGBB` (hex)

#### `PUT /chapters/{chapter_id}/content`
Update chapter content.

**Request Body:**
```json
{
  "content": "New chapter text content",
  "format": "text"
}
```

**Format options:**
- `text` - Plain text (converted to HTML paragraphs)
- `html` - Raw HTML content

#### `GET /chapters/{chapter_id}/text`
Get chapter content as plain text (HTML stripped).

**Response:**
```json
{
  "chapter_id": 1,
  "text": "Plain text content..."
}
```

#### `POST /chapters/{chapter_id}/scene-break`
Insert a scene break (`* * *`).

**Request Body:**
```json
{
  "position": -1
}
```

**Position:** `-1` = end of chapter

#### `POST /chapters/{chapter_id}/open`
Open chapter in the editor dock.

#### `POST /chapters/{chapter_id}/close`
Close chapter editor.

---

### Encyclopedia

#### `GET /projects/{project_id}/encyclopedia`
List encyclopedia entries.

**Query Parameters:**
- `category` (optional) - Filter by category

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "project_id": 1,
    "name": "John Smith",
    "category": "Character",
    "tags": "protagonist, hero",
    "created_at": "2025-01-10T08:00:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

#### `GET /projects/{project_id}/encyclopedia/search`
Search entries.

**Query Parameters:**
- `q` (required) - Search query

Searches name, content, and tags.

#### `GET /projects/{project_id}/encyclopedia/categories`
List all categories in use.

**Response:**
```json
["Character", "Location", "Item", "Event"]
```

#### `POST /projects/{project_id}/encyclopedia`
Create an entry.

**Request Body:**
```json
{
  "name": "Dragon",
  "category": "Creature",
  "content": "A fire-breathing beast",
  "tags": "monster, antagonist"
}
```

#### `GET /encyclopedia/{entry_id}`
Get entry details including content.

#### `PUT /encyclopedia/{entry_id}`
Update an entry.

**Request Body:**
```json
{
  "name": "Updated Name",
  "category": "NewCategory",
  "content": "Updated content",
  "tags": "new, tags"
}
```

#### `DELETE /encyclopedia/{entry_id}`
Delete an entry.

#### `POST /encyclopedia/{entry_id}/open`
Open entry in editor.

#### `POST /encyclopedia/{entry_id}/close`
Close entry editor.

---

### Canvas

#### `GET /stories/{story_id}/canvas`
Get canvas view state.

**Response:**
```json
{
  "story_id": 1,
  "pan_x": 0.0,
  "pan_y": 0.0,
  "zoom": 1.0
}
```

#### `PUT /stories/{story_id}/canvas/pan`
Pan the canvas.

**Request Body:**
```json
{
  "x": 100.0,
  "y": 200.0
}
```

#### `PUT /stories/{story_id}/canvas/zoom`
Set zoom level.

**Request Body:**
```json
{
  "zoom": 1.5
}
```

**Range:** 0.1 to 3.0

#### `POST /stories/{story_id}/canvas/focus`
Focus on a specific chapter.

**Request Body:**
```json
{
  "chapter_id": 5
}
```

#### `POST /stories/{story_id}/canvas/fit`
Fit all chapters in view.

#### `GET /stories/{story_id}/canvas/layout`
Get all chapter positions.

**Response:**
```json
{
  "story_id": 1,
  "chapters": [
    {"id": 1, "title": "Ch 1", "board_x": 100, "board_y": 100, "color": "#FFFF88"},
    {"id": 2, "title": "Ch 2", "board_x": 300, "board_y": 100, "color": "#88FF88"}
  ]
}
```

#### `POST /stories/{story_id}/canvas/reset`
Reset canvas to default view.

---

### State

#### `GET /state`
Get current application state.

**Response:**
```json
{
  "current_project_id": 1,
  "current_story_id": 2,
  "open_editors": [
    {"editor_type": "chapter", "item_id": 5, "is_modified": true},
    {"editor_type": "encyclopedia", "item_id": 3, "is_modified": false}
  ]
}
```

#### `GET /state/editors`
List open editors.

#### `POST /state/save-all`
Save all unsaved changes.

**Response:**
```json
{
  "items_saved": 2,
  "success": true,
  "message": "Saved 2 items"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid input) |
| 404 | Not Found |
| 409 | Conflict (e.g., story is locked) |
| 422 | Validation Error |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## OpenAPI Specification

The full OpenAPI spec is available at:
- **Swagger UI:** `http://127.0.0.1:5000/docs`
- **ReDoc:** `http://127.0.0.1:5000/redoc`
- **OpenAPI JSON:** `http://127.0.0.1:5000/openapi.json`

These are only available when BlueWriter is running.
