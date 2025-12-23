# BlueWriter MCP Tools Reference

This document describes all MCP (Model Context Protocol) tools available for controlling BlueWriter through AI assistants like Claude.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Tool Categories](#tool-categories)
  - [Project Tools](#project-tools)
  - [Story Tools](#story-tools)
  - [Chapter Tools](#chapter-tools)
  - [Encyclopedia Tools](#encyclopedia-tools)
  - [Canvas Tools](#canvas-tools)
  - [State Tools](#state-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

BlueWriter provides **46 MCP tools** organized into 6 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| Project | 6 | Create, manage, and open projects |
| Story | 9 | Manage stories, publishing, ordering |
| Chapter | 13 | CRUD, positioning, content editing |
| Encyclopedia | 9 | World-building entries and search |
| Canvas | 6 | Pan, zoom, focus, layout |
| State | 3 | App state, editors, save |

---

## Setup

### Prerequisites

1. BlueWriter must be running (the app, not just the MCP server)
2. The REST API runs on `http://127.0.0.1:5000`

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/.config/claude-desktop/config.json` on Linux):

```json
{
  "mcpServers": {
    "bluewriter": {
      "command": "python",
      "args": ["-m", "bluewriter_mcp.bluewriter_server"],
      "cwd": "/path/to/BlueWriter",
      "env": {
        "PYTHONPATH": "/path/to/BlueWriter"
      }
    }
  }
}
```

**Important:** Replace `/path/to/BlueWriter` with your actual installation path.

### Verification

After restarting Claude Desktop, you should see "bluewriter" in the MCP servers list. Try:

> "List my BlueWriter projects"

---

## Tool Categories

### Project Tools

#### `list_projects`
List all BlueWriter projects.

**Returns:** JSON array of projects with id, name, description, timestamps.

**Example:**
```
> List my projects
Found 2 projects:
1. "My Novel" - A science fiction epic
2. "Short Stories" - Collection of short fiction
```

---

#### `get_project`
Get details of a specific project.

**Parameters:**
- `project_id` (int, required) - The project ID

---

#### `create_project`
Create a new project.

**Parameters:**
- `name` (str, required) - Project name
- `description` (str, optional) - Project description

**Example:**
```
> Create a new project called "Fantasy Epic" with description "An epic fantasy trilogy"
Created project "Fantasy Epic" (ID: 3)
```

---

#### `update_project`
Update a project's name or description.

**Parameters:**
- `project_id` (int, required)
- `name` (str, optional)
- `description` (str, optional)

---

#### `delete_project`
Delete a project and ALL its contents (stories, chapters, encyclopedia entries).

**Parameters:**
- `project_id` (int, required)

**Warning:** This is irreversible!

---

#### `open_project`
Open/select a project in the BlueWriter UI.

**Parameters:**
- `project_id` (int, required)

---

### Story Tools

#### `list_stories`
List all stories in a project.

**Parameters:**
- `project_id` (int, required)

**Returns:** Array with id, title, synopsis, status, sort_order

---

#### `get_story`
Get story details.

**Parameters:**
- `story_id` (int, required)

---

#### `create_story`
Create a new story in a project.

**Parameters:**
- `project_id` (int, required)
- `title` (str, required)
- `synopsis` (str, optional)

---

#### `update_story`
Update story title or synopsis.

**Parameters:**
- `story_id` (int, required)
- `title` (str, optional)
- `synopsis` (str, optional)

**Note:** Cannot update `final_published` stories.

---

#### `delete_story`
Delete a story and all its chapters.

**Parameters:**
- `story_id` (int, required)

---

#### `select_story`
Select a story in the UI (displays chapters on canvas).

**Parameters:**
- `story_id` (int, required)

---

#### `publish_story`
Publish a story.

**Parameters:**
- `story_id` (int, required)
- `final` (bool, optional, default: false)
  - `false` → rough_published (still editable)
  - `true` → final_published (locked)

---

#### `unpublish_story`
Unpublish and unlock a story.

**Parameters:**
- `story_id` (int, required)

---

#### `reorder_stories`
Change story order in project.

**Parameters:**
- `project_id` (int, required)
- `story_ids` (list[int], required) - Story IDs in desired order

---

### Chapter Tools

#### `list_chapters`
List all chapters in a story.

**Parameters:**
- `story_id` (int, required)

**Returns:** Array with id, title, summary, board_x, board_y, color

---

#### `get_chapter`
Get chapter details including content.

**Parameters:**
- `chapter_id` (int, required)

---

#### `create_chapter`
Create a new chapter (appears as sticky note on canvas).

**Parameters:**
- `story_id` (int, required)
- `title` (str, required)
- `board_x` (int, optional, default: 100)
- `board_y` (int, optional, default: 100)
- `color` (str, optional, default: "#FFFF88")

**Colors:** Use hex format like "#FF8888" (red), "#88FF88" (green), "#8888FF" (blue)

---

#### `update_chapter`
Update chapter title or summary.

**Parameters:**
- `chapter_id` (int, required)
- `title` (str, optional)
- `summary` (str, optional)

---

#### `delete_chapter`
Delete a chapter.

**Parameters:**
- `chapter_id` (int, required)

---

#### `move_chapter`
Move chapter's sticky note on the canvas.

**Parameters:**
- `chapter_id` (int, required)
- `x` (int, required) - New X position
- `y` (int, required) - New Y position

**Note:** Negative coordinates are allowed.

---

#### `set_chapter_color`
Change sticky note color.

**Parameters:**
- `chapter_id` (int, required)
- `color` (str, required) - Hex color like "#FF8888"

---

#### `open_chapter`
Open chapter in the editor dock.

**Parameters:**
- `chapter_id` (int, required)

---

#### `close_chapter`
Close chapter editor.

**Parameters:**
- `chapter_id` (int, required)

---

#### `get_chapter_text`
Get chapter content as plain text (HTML stripped).

**Parameters:**
- `chapter_id` (int, required)

**Returns:** Plain text content

---

#### `set_chapter_content`
Set chapter content.

**Parameters:**
- `chapter_id` (int, required)
- `content` (str, required) - The content to set
- `format` (str, optional, default: "text")
  - `"text"` - Plain text (converted to HTML paragraphs)
  - `"html"` - Raw HTML

---

#### `insert_scene_break`
Insert a scene break (`* * *`) at the end of the chapter.

**Parameters:**
- `chapter_id` (int, required)

---

### Encyclopedia Tools

#### `list_encyclopedia_entries`
List encyclopedia entries.

**Parameters:**
- `project_id` (int, required)
- `category` (str, optional) - Filter by category

---

#### `get_encyclopedia_entry`
Get entry details including content.

**Parameters:**
- `entry_id` (int, required)

---

#### `create_encyclopedia_entry`
Create a new encyclopedia entry.

**Parameters:**
- `project_id` (int, required)
- `name` (str, required) - Entry name
- `category` (str, required) - Category (Character, Location, Item, etc.)
- `content` (str, optional) - Description/content
- `tags` (str, optional) - Comma-separated tags

**Common Categories:** Character, Location, Item, Faction, Event, Concept

---

#### `update_encyclopedia_entry`
Update an entry.

**Parameters:**
- `entry_id` (int, required)
- `name` (str, optional)
- `category` (str, optional)
- `content` (str, optional)
- `tags` (str, optional)

---

#### `delete_encyclopedia_entry`
Delete an entry.

**Parameters:**
- `entry_id` (int, required)

---

#### `search_encyclopedia`
Search entries by keyword.

**Parameters:**
- `project_id` (int, required)
- `query` (str, required) - Search term

Searches name, content, and tags.

---

#### `list_categories`
List all categories in use.

**Parameters:**
- `project_id` (int, required)

---

#### `open_encyclopedia_entry`
Open entry in editor.

**Parameters:**
- `entry_id` (int, required)

---

#### `close_encyclopedia_entry`
Close entry editor.

**Parameters:**
- `entry_id` (int, required)

---

### Canvas Tools

#### `get_canvas_view`
Get current canvas pan and zoom state.

**Parameters:**
- `story_id` (int, required)

**Returns:** pan_x, pan_y, zoom

---

#### `pan_canvas`
Pan the canvas to specific coordinates.

**Parameters:**
- `story_id` (int, required)
- `x` (float, required)
- `y` (float, required)

---

#### `zoom_canvas`
Set canvas zoom level.

**Parameters:**
- `story_id` (int, required)
- `zoom` (float, required) - Range: 0.1 to 3.0 (1.0 = 100%)

---

#### `focus_chapter`
Pan and zoom to center a specific chapter.

**Parameters:**
- `story_id` (int, required)
- `chapter_id` (int, required)

---

#### `fit_all_chapters`
Zoom and pan to fit all chapters in view.

**Parameters:**
- `story_id` (int, required)

---

#### `get_canvas_layout`
Get all chapter positions on the canvas.

**Parameters:**
- `story_id` (int, required)

**Returns:** Array of chapters with positions and colors

---

### State Tools

#### `get_app_state`
Get current BlueWriter application state.

**Returns:**
- `current_project_id` - Currently open project (or null)
- `current_story_id` - Currently selected story (or null)
- `open_editors` - List of open editors

---

#### `list_open_editors`
List all currently open editors.

**Returns:** Array of {editor_type, item_id, is_modified}

---

#### `save_all`
Save all unsaved changes in open editors.

**Returns:** Number of items saved

---

## Examples

### Creating a Story Structure

```
User: Create a new story called "The Journey" in project 1 with three chapters

Claude: I'll create that story and chapters for you.

[Creates story, gets story_id=5]
[Creates "Chapter 1: The Beginning" at position (100, 100)]
[Creates "Chapter 2: The Middle" at position (300, 100)]
[Creates "Chapter 3: The End" at position (500, 100)]

Done! I've created "The Journey" with three chapters arranged horizontally on the canvas.
```

### Writing Chapter Content

```
User: Write the opening paragraph for chapter 1

Claude: I'll add that content now.

[Uses set_chapter_content with format="text"]

The chapter has been updated with the opening paragraph. Would you like me to open it in the editor so you can see it?
```

### Organizing with Encyclopedia

```
User: Create character entries for the main characters in my story

Claude: I'll create encyclopedia entries for your characters.

[Creates entries with category="Character"]

Created 3 character entries:
- John Smith (protagonist)
- Sarah Jones (ally)  
- The Shadow (antagonist)

You can search for them anytime with "search encyclopedia for [name]".
```

---

## Troubleshooting

### "Connection refused" errors

**Cause:** BlueWriter is not running or API server hasn't started.

**Solution:** 
1. Launch BlueWriter application
2. Wait a few seconds for API to initialize
3. Verify by visiting `http://127.0.0.1:5000/health` in a browser

### "Module not found" errors

**Cause:** PYTHONPATH not set correctly in Claude Desktop config.

**Solution:** Ensure your config includes:
```json
"env": {
  "PYTHONPATH": "/path/to/BlueWriter"
}
```

### Changes not appearing in UI

**Cause:** Event system not connected (rare).

**Solution:** 
1. Try `save_all` to force a sync
2. Restart BlueWriter if issues persist

### "Story is locked" errors

**Cause:** Trying to modify a `final_published` story.

**Solution:** Use `unpublish_story` first to unlock it.

### Canvas not updating

**Cause:** Story not selected in UI.

**Solution:** Use `select_story` to ensure the story is displayed on canvas.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01 | Initial release with 46 tools |
