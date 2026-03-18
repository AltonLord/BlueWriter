# BLU-002: Unified Canvas with Story Groupings

**Status:** Ready for Implementation  
**Priority:** High  
**Version Target:** v1.1.0-beta1  
**Author:** BlueWriter Engineering Manager  
**Date:** 2025-01-25

---

## Overview

Replace the current per-story canvas (tabs in sidebar, separate canvas per story) with a **single unified project canvas** where all chapters exist in one space. Stories become visual **groupings** on the canvas — either a **bounding box** (rectangle) or a **string** (ordered path connecting chapters). Unassigned chapters (orphans) are valid and live freely on the canvas.

This supports the writer's workflow of creating side-stories, research chapters, and backstory material that informs the main narrative but may never be read by an audience.

---

## Current State (What Exists Today)

### Architecture
- `views/story_manager.py` — `StoryManagerWidget`: Tab-based UI in left sidebar. One tab per story. Each tab shows title + synopsis editor.
- `views/timeline_canvas.py` — `TimelineCanvas`: Single canvas, only shows chapters for the **selected story**.
- `views/main_window.py` — Wires story selection → canvas reload.
- `models/chapter.py` — `story_id INTEGER NOT NULL` (required foreign key).
- `models/story.py` — No visual representation fields.
- `database/schema.py` — `CHAPTERS_TABLE_SQL` has `story_id NOT NULL`.

### Current Flow
```
Project selected → StoryManagerWidget loads tabs → Tab selected → Canvas loads that story's chapters
```

### Current Limitations
- Switching stories clears the canvas — writer loses spatial context.
- No way to have "orphan" chapters outside a story.
- No visual relationship between stories on canvas.

---

## Target State (What To Build)

### New Flow
```
Project selected → Unified canvas loads ALL chapters → Stories shown as overlays (boxes/strings)
```

### Left Sidebar: Story Cards Panel
Replaces `StoryManagerWidget` tabs with a **vertical card list** (bottom-to-top stacking, newest at top).

Each card:
```
┌─────────────────────────────────────────┐
│  [●] Story Title                [⋮]     │  ← colored dot = box/string indicator
│  ─────────────────────────────────────  │
│  Synopsis text truncated to 2 lines...  │
│                                         │
│  [Edit Outline]                         │
└─────────────────────────────────────────┘
```

- **[⋮] button** → context menu: "Edit Metadata", "Delete Story" (does NOT delete chapters)
- **[Edit Outline] button** → enters outline-edit mode for that story on the canvas
- **Double-click card** → canvas animates to frame/zoom to show that story's chapters
- **Right-click card** → same context menu as [⋮]
- **"+ New Story" button** stays at top of panel (above card list)

### Canvas: Story Grouping Overlays

Two representation types drawn **underneath** sticky notes:

#### Type 1: Box
- Semi-transparent filled rectangle with colored border
- Border color: story-specific (auto-assigned from palette, or user-set in metadata)
- Title label in top-left corner of box
- In edit mode: resize handles on corners and edges, drag to reposition

#### Type 2: String (Red Yarn)
- A red yarn-textured path connecting chapter sticky notes in order
- Rendered as a curved/bezier line with yarn texture (NOT 3D — use QPainter with texture brush or stippled red line with slight wobble to simulate yarn)
- Yarn connects chapters in the order defined in `bounding_data`
- In edit mode: click chapters in sequence to define/reorder the string path
- Highlighted (brighter red, thicker) when the story card is hovered or in edit mode

### Canvas Behavior Changes
- On project open: load ALL chapters across all stories onto one canvas
- Story overlays (boxes/strings) drawn first, sticky notes on top
- Double-click story card → `fit_story_in_view()`: pan + zoom to frame that story's bounding box/string extent
- Orphan chapters (no story) are visible and fully functional on canvas

---

## Database Changes

### 1. Make `chapters.story_id` nullable

**Migration in `database/schema.py` → `migrate_database()`:**

```python
# Migration: Make story_id nullable in chapters
cursor.execute("PRAGMA table_info(chapters)")
chapter_cols = {col[1]: col for col in cursor.fetchall()}

# Check if story_id is still NOT NULL (old schema)
# SQLite doesn't support ALTER COLUMN, so we recreate the table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chapters_new'")
if not cursor.fetchone():
    # Check if migration needed by checking nullable status
    # story_id column notnull flag: 1 = NOT NULL, 0 = nullable
    if chapter_cols.get('story_id', [None,None,None,None,None,1])[3] == 1:
        # Recreate table with nullable story_id
        cursor.execute("""
            CREATE TABLE chapters_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER,  -- nullable: chapters can be orphans
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                board_x REAL DEFAULT 100.0,
                board_y REAL DEFAULT 100.0,
                sort_order INTEGER DEFAULT 0,
                color TEXT DEFAULT '#FFFF88',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("""
            INSERT INTO chapters_new 
            SELECT id, story_id, title, summary, content, board_x, board_y, 
                   sort_order, color, created_at, updated_at 
            FROM chapters
        """)
        cursor.execute("DROP TABLE chapters")
        cursor.execute("ALTER TABLE chapters_new RENAME TO chapters")
        connection.commit()
```

### 2. Add story visual representation fields

**In `migrate_database()`:**

```python
cursor.execute("PRAGMA table_info(stories)")
story_cols = [col[1] for col in cursor.fetchall()]

if 'representation_type' not in story_cols:
    cursor.execute("ALTER TABLE stories ADD COLUMN representation_type TEXT DEFAULT 'box'")
    connection.commit()

if 'bounding_data' not in story_cols:
    cursor.execute("ALTER TABLE stories ADD COLUMN bounding_data TEXT")
    connection.commit()

if 'outline_color' not in story_cols:
    cursor.execute("ALTER TABLE stories ADD COLUMN outline_color TEXT DEFAULT '#4A90D9'")
    connection.commit()
```

### 3. `bounding_data` JSON format

**Box type:**
```json
{"x1": 100, "y1": 80, "x2": 600, "y2": 450}
```

**String type:**
```json
{"chapter_ids": [3, 1, 5, 2]}
```
(Ordered list of chapter IDs defining the yarn path sequence)

---

## Model Changes

### `models/story.py`

Add new fields to `Story` dataclass:
```python
representation_type: str = "box"   # "box" or "string"
bounding_data: Optional[str] = None  # JSON string (see format above)
outline_color: str = "#4A90D9"      # hex color for box border / string color hint
```

Update `STORY_COLUMNS` to include new fields.  
Update `_from_row()`, `create()`, `update()` to handle new fields.

### `models/chapter.py`

Change `story_id` field:
```python
story_id: Optional[int] = None   # was: story_id: int = 0
```

Update `create()` to accept `story_id: Optional[int] = None`.

---

## Service Changes

### `services/story_service.py`

**`StoryDTO`** — add fields:
```python
representation_type: str
bounding_data: Optional[str]
outline_color: str
```

Add methods:
```python
def update_story_outline(
    self,
    story_id: int,
    representation_type: Optional[str] = None,
    bounding_data: Optional[str] = None,
    outline_color: Optional[str] = None,
) -> StoryDTO:
    """Update the visual outline data for a story."""
    ...

def get_stories_for_canvas(self, project_id: int) -> List[StoryDTO]:
    """Get all stories with their visual data for canvas rendering.
    Same as list_stories() but name makes intent clear."""
    return self.list_stories(project_id)
```

### `services/chapter_service.py`

**`ChapterDTO`** — change field:
```python
story_id: Optional[int]   # was: story_id: int
```

**`create_chapter()`** — change signature:
```python
def create_chapter(
    self,
    story_id: Optional[int] = None,   # was: story_id: int (required)
    title: str = "",
    board_x: float = 100.0,
    board_y: float = 100.0,
    color: str = "#FFFF88",
) -> ChapterDTO:
```

Remove `_check_story_not_locked()` call when `story_id is None`.

Add method:
```python
def list_all_chapters_for_project(self, project_id: int) -> List[ChapterDTO]:
    """Get ALL chapters across all stories in a project, plus orphan chapters.
    
    Used by the unified canvas to load everything at once.
    """
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.* FROM chapters c
            LEFT JOIN stories s ON c.story_id = s.id
            WHERE s.project_id = ? OR (c.story_id IS NULL AND /* need project context */ 1=0)
            ORDER BY c.created_at ASC
        """, (project_id,))
        # NOTE: Orphan chapters need a project_id column OR we add a project_id 
        # directly to chapters. See design note below.
        ...
```

> **⚠️ Design Note — Orphan Chapter Project Context:**  
> When `story_id IS NULL`, we have no way to know which project a chapter belongs to.  
> **Solution:** Add `project_id` column to `chapters` table (nullable for backward compat, populated for new chapters and backfilled in migration).
>
> Add to migration:
> ```sql
> ALTER TABLE chapters ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE;
> UPDATE chapters SET project_id = (SELECT project_id FROM stories WHERE stories.id = chapters.story_id);
> ```

### `services/canvas_service.py`

Change from **per-story** view state to **per-project** view state:

```python
# Change key from story_id to project_id
self._views: Dict[int, CanvasViewDTO] = {}  # keyed by project_id now

def get_view(self, project_id: int) -> CanvasViewDTO: ...
def set_pan(self, project_id: int, x: float, y: float) -> CanvasViewDTO: ...
def set_zoom(self, project_id: int, zoom: float) -> CanvasViewDTO: ...

def frame_story(
    self,
    project_id: int,
    story_dto: StoryDTO,
    chapter_positions: List[tuple],
    viewport_width: int = 800,
    viewport_height: int = 600,
) -> CanvasViewDTO:
    """Pan and zoom canvas to frame a specific story's chapters.
    
    Called when user double-clicks a story card.
    Calculates bounding box from story's bounding_data or chapter positions,
    then animates (or jumps) to frame that area.
    """
    ...
```

---

## View Changes

### `views/story_manager.py` → Rename/Replace: `views/story_panel.py`

Create new `StoryPanelWidget(QWidget)` to replace `StoryManagerWidget`.

**Layout:**
```
QVBoxLayout
├── QPushButton("+ New Story")
└── QScrollArea
    └── QWidget (cards container)
        └── QVBoxLayout (cards stacked, newest at top)
            ├── StoryCard(story_1)
            ├── StoryCard(story_2)
            └── ...
```

**`StoryCard(QFrame)` widget:**
```python
class StoryCard(QFrame):
    outline_edit_requested = Signal(int)   # story_id
    frame_story_requested = Signal(int)    # story_id  
    delete_requested = Signal(int)         # story_id
    edit_metadata_requested = Signal(int)  # story_id
    
    def __init__(self, story_dto: StoryDTO, parent=None):
        # Card visual: QFrame with styled border matching story outline_color
        # Contains: colored dot, title label, synopsis label (2 lines, elided)
        # [Edit Outline] button at bottom
        # [⋮] menu button top-right
        ...
    
    def mouseDoubleClickEvent(self, event):
        self.frame_story_requested.emit(self.story_id)
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Edit Metadata", lambda: self.edit_metadata_requested.emit(self.story_id))
        menu.addSeparator()
        delete_action = menu.addAction("Delete Story")
        delete_action.setToolTip("Removes story grouping. Chapters are kept.")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.story_id))
        menu.exec(event.globalPos())
```

**Story Metadata Dialog** (`views/story_metadata_dialog.py`):
```python
class StoryMetadataDialog(QDialog):
    """Dialog for editing story title, synopsis, representation type, color."""
    
    def __init__(self, story_dto: StoryDTO, parent=None):
        # Fields:
        # - Title (QLineEdit)
        # - Synopsis (QTextEdit)
        # - Representation Type (QComboBox: "Box" / "String")
        # - Outline Color (color picker button showing current color)
        # - OK / Cancel buttons
        ...
```

### `views/timeline_canvas.py` → Major Refactor

**New responsibilities:**
1. Load and render ALL chapters for a project (not just one story)
2. Render story overlays (boxes and strings) beneath sticky notes
3. Support outline-edit mode for drawing/editing a story's bounding box or string path
4. Emit signals for story overlay interactions

**New signals:**
```python
story_outline_updated = Signal(int, str)  # story_id, bounding_data JSON
outline_edit_mode_changed = Signal(bool)  # True = editing, False = normal
```

**New methods:**
```python
def load_project(self, project_id: int, chapters: List[ChapterDTO], stories: List[StoryDTO]) -> None:
    """Load all chapters and stories for a project onto the canvas."""
    ...

def enter_outline_edit_mode(self, story_id: int) -> None:
    """Enter edit mode for a specific story's outline.
    
    Box mode: Shows resize handles on the story's bounding box.
    String mode: Highlights chapters; click order defines string path.
    Pressing Escape or clicking [Done] exits edit mode.
    """
    ...

def exit_outline_edit_mode(self) -> None:
    """Exit outline edit mode and emit story_outline_updated signal."""
    ...

def frame_story(self, story_dto: StoryDTO, chapters: List[ChapterDTO]) -> None:
    """Animate canvas to frame a specific story's chapters in view."""
    ...
```

**Drawing additions to `paintEvent()`:**
```python
def draw_story_overlays(self, painter: QPainter) -> None:
    """Draw all story boxes and strings beneath sticky notes."""
    for story in self._stories:
        if story.representation_type == 'box':
            self._draw_story_box(painter, story)
        elif story.representation_type == 'string':
            self._draw_story_string(painter, story)

def _draw_story_box(self, painter: QPainter, story: StoryDTO) -> None:
    """Draw semi-transparent filled rectangle with colored border."""
    if not story.bounding_data:
        return
    data = json.loads(story.bounding_data)
    rect = QRectF(data['x1'], data['y1'], data['x2'] - data['x1'], data['y2'] - data['y1'])
    
    # Fill: very light tint of outline_color at ~15% opacity
    fill_color = QColor(story.outline_color)
    fill_color.setAlpha(38)  # ~15%
    painter.fillRect(rect, fill_color)
    
    # Border
    border_color = QColor(story.outline_color)
    pen = QPen(border_color, 2, Qt.DashLine)
    painter.setPen(pen)
    painter.drawRect(rect)
    
    # Title label top-left
    painter.setPen(QPen(border_color))
    font = QFont()
    font.setBold(True)
    font.setPointSize(10)
    painter.setFont(font)
    painter.drawText(int(data['x1']) + 8, int(data['y1']) + 20, story.title)

def _draw_story_string(self, painter: QPainter, story: StoryDTO) -> None:
    """Draw red yarn path connecting chapters in order.
    
    Yarn effect: Draw a thick semi-transparent red line with a 
    slightly offset thinner line to create a two-strand rope illusion.
    Use a slight bezier curve between points for organic feel.
    No 3D texture — pure QPainter.
    """
    if not story.bounding_data:
        return
    data = json.loads(story.bounding_data)
    chapter_ids = data.get('chapter_ids', [])
    
    # Get chapter center positions in order
    points = []
    for cid in chapter_ids:
        chapter = self._chapter_map.get(cid)
        if chapter:
            # Center of sticky note (assume ~150x100 size)
            cx = chapter.board_x + 75
            cy = chapter.board_y + 50
            points.append(QPointF(cx, cy))
    
    if len(points) < 2:
        return
    
    is_editing = (self._edit_mode_story_id == story.id)
    
    # Yarn strand 1 (main, darker red)
    yarn_color_1 = QColor(220, 30, 30, 200 if is_editing else 160)
    # Yarn strand 2 (offset, lighter red — gives twisted look)
    yarn_color_2 = QColor(255, 80, 80, 150 if is_editing else 100)
    
    line_width = 4 if is_editing else 3
    
    path = QPainterPath(points[0])
    for i in range(1, len(points)):
        # Bezier curve: control point is midpoint offset slightly
        mid_x = (points[i-1].x() + points[i].x()) / 2
        mid_y = (points[i-1].y() + points[i].y()) / 2 - 20  # slight upward bow
        path.quadTo(QPointF(mid_x, mid_y), points[i])
    
    # Draw strand 2 (offset by 2px)
    painter.save()
    painter.translate(2, 2)
    painter.setPen(QPen(yarn_color_2, line_width - 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)
    painter.restore()
    
    # Draw strand 1
    painter.setPen(QPen(yarn_color_1, line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)
    
    # Draw story title near first point
    painter.setPen(QPen(QColor(180, 20, 20)))
    font = QFont()
    font.setBold(True)
    font.setPointSize(9)
    painter.setFont(font)
    painter.drawText(int(points[0].x()) + 10, int(points[0].y()) - 10, story.title)
```

### `views/main_window.py` — Wiring Changes

- Replace `StoryManagerWidget` with `StoryPanelWidget` in left sidebar
- On project open: call `canvas.load_project(project_id, all_chapters, all_stories)`
- Connect `StoryCard.frame_story_requested` → `canvas.frame_story()`
- Connect `StoryCard.outline_edit_requested` → `canvas.enter_outline_edit_mode()`
- Connect `canvas.story_outline_updated` → `story_service.update_story_outline()`
- Connect `StoryCard.edit_metadata_requested` → open `StoryMetadataDialog`
- Connect `StoryCard.delete_requested` → confirm dialog → `story_service.delete_story()` (chapters kept)
- Remove story-tab-based canvas reload logic

---

## API Changes

### `api/routes/stories.py`

Add endpoint:
```python
@router.patch("/{story_id}/outline")
async def update_story_outline(story_id: int, body: StoryOutlineUpdate):
    """Update a story's visual outline data (bounding_data, representation_type, outline_color)."""
    ...
```

Add schema in `api/schemas.py`:
```python
class StoryOutlineUpdate(BaseModel):
    representation_type: Optional[str] = None  # "box" or "string"
    bounding_data: Optional[str] = None         # JSON string
    outline_color: Optional[str] = None         # hex color
```

### `api/routes/chapters.py`

- `POST /chapters` — `story_id` becomes optional in request body
- `GET /projects/{project_id}/chapters` — **new endpoint** returning all chapters for a project

Add schema:
```python
class ChapterCreate(BaseModel):
    story_id: Optional[int] = None   # was required
    title: str
    board_x: float = 100.0
    board_y: float = 100.0
    color: str = "#FFFF88"
```

---

## Migration for Existing Projects

In `migrate_database()`, after schema changes:

```python
# Backfill project_id on chapters from their story's project
cursor.execute("""
    UPDATE chapters 
    SET project_id = (
        SELECT stories.project_id 
        FROM stories 
        WHERE stories.id = chapters.story_id
    )
    WHERE project_id IS NULL AND story_id IS NOT NULL
""")

# Auto-create bounding boxes for existing stories
# Find bounding box of all chapters in each story, add 50px padding
cursor.execute("""
    SELECT s.id, MIN(c.board_x), MIN(c.board_y), MAX(c.board_x), MAX(c.board_y)
    FROM stories s
    JOIN chapters c ON c.story_id = s.id
    WHERE s.bounding_data IS NULL
    GROUP BY s.id
""")
rows = cursor.fetchall()
for story_id, min_x, min_y, max_x, max_y in rows:
    if min_x is not None:
        import json
        padding = 80
        bounding_data = json.dumps({
            "x1": min_x - padding,
            "y1": min_y - padding,
            "x2": max_x + 150 + padding,  # 150 = sticky note width
            "y2": max_y + 100 + padding    # 100 = sticky note height
        })
        cursor.execute(
            "UPDATE stories SET bounding_data = ?, representation_type = 'box' WHERE id = ?",
            (bounding_data, story_id)
        )
connection.commit()
```

---

## Events

Add to `events/events.py`:
```python
@dataclass
class StoryOutlineUpdated:
    story_id: int
    representation_type: str
    bounding_data: Optional[str]

@dataclass  
class ProjectCanvasLoaded:
    project_id: int
    chapter_count: int
    story_count: int
```

---

## MCP Tool Updates

### `bluewriter_mcp/tools/` — Story tools

Add MCP tool: `update_story_outline`
```
Parameters: story_id, representation_type, bounding_data, outline_color
Returns: Updated StoryDTO
```

Add MCP tool: `list_project_chapters`
```
Parameters: project_id
Returns: All chapters across all stories + orphans for a project
```

---

## File Change Summary

| File | Change Type | Notes |
|------|-------------|-------|
| `database/schema.py` | Modify | Add migrations for nullable story_id, new story columns, project_id on chapters |
| `models/story.py` | Modify | Add 3 new fields, update STORY_COLUMNS, _from_row, create, update |
| `models/chapter.py` | Modify | story_id Optional, add project_id field |
| `services/story_service.py` | Modify | StoryDTO new fields, add update_story_outline() |
| `services/chapter_service.py` | Modify | story_id Optional, add list_all_chapters_for_project() |
| `services/canvas_service.py` | Modify | Switch from per-story to per-project view state, add frame_story() |
| `views/story_manager.py` | Replace | New StoryPanelWidget with StoryCard components |
| `views/story_panel.py` | **New** | StoryPanelWidget + StoryCard classes |
| `views/story_metadata_dialog.py` | **New** | StoryMetadataDialog |
| `views/timeline_canvas.py` | Modify | Unified canvas, story overlays, outline edit mode |
| `views/main_window.py` | Modify | Wire new panel + canvas, remove old tab-based flow |
| `api/schemas.py` | Modify | StoryOutlineUpdate, updated ChapterCreate |
| `api/routes/stories.py` | Modify | Add PATCH /{story_id}/outline |
| `api/routes/chapters.py` | Modify | story_id optional, add GET /projects/{id}/chapters |
| `events/events.py` | Modify | Add StoryOutlineUpdated, ProjectCanvasLoaded |
| `bluewriter_mcp/tools/` | Modify | Add update_story_outline, list_project_chapters tools |

---

## Implementation Order

Implement in this sequence to avoid breaking the running app:

1. **Database migrations** — schema.py (foundation, non-breaking)
2. **Model updates** — story.py, chapter.py (data layer)
3. **Service updates** — story_service.py, chapter_service.py, canvas_service.py
4. **New views** — story_panel.py, story_metadata_dialog.py (new files, no breakage)
5. **Canvas refactor** — timeline_canvas.py (largest change)
6. **Main window wiring** — main_window.py (final integration)
7. **API updates** — schemas.py, routes (REST layer)
8. **MCP tools** — new tools (last, depends on API)
9. **Tests** — update existing tests, add new tests for all new behavior

---

## Tests Required

- `tests/test_story_service.py` — test `update_story_outline()`, test `delete_story()` keeps chapters
- `tests/test_chapter_service.py` — test orphan chapter creation (no story_id), test `list_all_chapters_for_project()`
- `tests/test_canvas_service.py` — test per-project view state, test `frame_story()`
- `tests/test_schema_migration.py` — test migration from old schema to new
- `tests/test_api_stories.py` — test new PATCH outline endpoint
- `tests/test_api_chapters.py` — test optional story_id, test new project chapters endpoint

---

## Acceptance Criteria

- [ ] All existing chapters remain visible and functional after migration
- [ ] Existing projects auto-get bounding boxes around their story chapters
- [ ] New chapters can be created without a story (orphans)
- [ ] Story cards appear in left sidebar as vertical card list
- [ ] Double-click story card → canvas frames that story
- [ ] Right-click story card → "Edit Metadata" and "Delete Story" options
- [ ] "Delete Story" removes story grouping but leaves chapters on canvas
- [ ] "Edit Outline" enters box-draw or string-path mode per story type
- [ ] Box overlay: semi-transparent fill, dashed colored border, title label
- [ ] String overlay: red yarn path (two-strand bezier, no 3D) connecting chapters in order
- [ ] String highlights (brighter, thicker) when story card is hovered or in edit mode
- [ ] Story metadata dialog: title, synopsis, representation type, color
- [ ] "+" New Story button still creates a new story
- [ ] All 197 existing tests still pass
- [ ] New tests added for all new behavior (target: 230+ tests)
- [ ] API endpoints updated and documented in docs/API.md
- [ ] MCP tools updated and documented in docs/MCP_TOOLS.md

---

## Notes for Claude Code

- **Do not break existing tests** — run `pytest tests/` before and after each major change
- **SQLite ALTER TABLE limitations** — SQLite cannot drop columns or change nullability directly. Use the recreate-table pattern shown in the migration section.
- **Qt painting order matters** — story overlays MUST be drawn in `paintEvent()` BEFORE sticky notes are positioned as child widgets. The overlays are painted on the canvas background; sticky notes are child QWidgets on top.
- **Yarn effect** — keep it simple. Two bezier paths offset by 2px with different opacity red. No image textures needed. The visual goal is "organic red thread", not photorealism.
- **Backward compatibility** — the migration must handle projects that have stories with chapters AND projects that have stories with no chapters (bounding_data stays NULL for empty stories).
- **`story_manager.py`** — keep the old file in place (rename to `story_manager_old.py`) until `main_window.py` is updated to use the new `story_panel.py`. This prevents a broken import state mid-implementation.
