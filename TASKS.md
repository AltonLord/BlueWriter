# BlueWriter - Task Specifications

**Project:** BlueWriter - Fiction Writing Aid
**Location:** /fast/BlueWriter/
**Tech Stack:** Python 3.10+, PySide6, SQLite

---

## CRITICAL RULES FOR ALL TASKS

1. **READ PROJECT_STATE.md FIRST** before starting any task
2. **UPDATE PROJECT_STATE.md** after completing each task
3. **Python ONLY** - No JavaScript, TypeScript, or web technologies
4. **PySide6 ONLY** - Do not use PyQt5, Tkinter, or other GUI frameworks
5. **Local/Offline ONLY** - No web APIs, cloud services, or network calls
6. **One task at a time** - Complete current task before moving to next
7. **Test before marking complete** - Code must run without errors

---

## DIRECTORY STRUCTURE TARGET

```
/fast/BlueWriter/
├── main.py
├── requirements.txt
├── PROJECT_STATE.md
├── TASKS.md
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── schema.py
│   └── migrations.py
├── models/
│   ├── __init__.py
│   ├── project.py
│   ├── story.py
│   ├── chapter.py
│   └── character.py
├── views/
│   ├── __init__.py
│   ├── main_window.py
│   ├── timeline_canvas.py
│   ├── sticky_note.py
│   ├── chapter_editor.py
│   ├── project_browser.py
│   └── story_selector.py
├── controllers/
│   ├── __init__.py
│   ├── canvas_controller.py
│   └── story_controller.py
├── utils/
│   ├── __init__.py
│   └── text_formatting.py
├── resources/
│   ├── styles.qss
│   └── icons/
└── data/
    └── (SQLite databases stored here)
```

---

## PHASE 1: FOUNDATION

### Task 1.1 - Create Directory Structure and Requirements

**Objective:** Set up project skeleton with all directories and dependencies.

**Create these directories:**
- /fast/BlueWriter/database/
- /fast/BlueWriter/models/
- /fast/BlueWriter/views/
- /fast/BlueWriter/controllers/
- /fast/BlueWriter/utils/
- /fast/BlueWriter/resources/
- /fast/BlueWriter/resources/icons/
- /fast/BlueWriter/data/

**Create these files:**

1. **requirements.txt**
```
PySide6>=6.5.0
```

2. **All __init__.py files** (empty files in each package directory)
- database/__init__.py
- models/__init__.py
- views/__init__.py
- controllers/__init__.py
- utils/__init__.py

**Acceptance Criteria:**
- [ ] All directories exist
- [ ] requirements.txt contains PySide6
- [ ] All __init__.py files created
- [ ] Can run: `pip install -r requirements.txt`

**After completing:** Update PROJECT_STATE.md - mark 1.1 complete, set current task to 1.2

---

### Task 1.2 - Database Connection Manager

**Objective:** Create SQLite connection manager with context manager support.

**Create file:** `/fast/BlueWriter/database/connection.py`

**Requirements:**


```python
"""
Database connection manager for BlueWriter.
Handles SQLite connections with context manager support.
"""
from pathlib import Path
from typing import Optional
import sqlite3

class DatabaseManager:
    """Manages SQLite database connections."""
    
    def __init__(self, db_path: Path) -> None:
        """Initialize with database file path."""
        ...
    
    def connect(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        ...
    
    def __enter__(self) -> sqlite3.Connection:
        """Context manager entry."""
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with commit/rollback."""
        ...

def get_default_db_path() -> Path:
    """Return default database path in data/ directory."""
    ...
```

**Key Implementation Details:**
- Store database files in `/fast/BlueWriter/data/` directory
- Enable foreign keys: `PRAGMA foreign_keys = ON`
- Use WAL mode for better concurrency: `PRAGMA journal_mode=WAL`
- Connection should auto-create the data/ directory if needed

**Acceptance Criteria:**
- [ ] DatabaseManager class implemented
- [ ] Context manager works (with statement)
- [ ] Foreign keys enabled on every connection
- [ ] Default path points to data/ directory
- [ ] No errors when instantiated

**After completing:** Update PROJECT_STATE.md - mark 1.2 complete, set current task to 1.3

---

### Task 1.3 - Schema Definition

**Objective:** Define all database tables with proper relationships.

**Create file:** `/fast/BlueWriter/database/schema.py`

**Tables to create:**

```sql
-- Projects table (series or standalone book container)
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stories table (individual books within a project)
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    synopsis TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Chapters table (the sticky notes)
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    board_x REAL DEFAULT 100.0,
    board_y REAL DEFAULT 100.0,
    sort_order INTEGER DEFAULT 0,
    color TEXT DEFAULT '#FFFF88',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
);

-- Characters table (shared across stories in a project)
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Character appearances (which chapters feature which characters)
CREATE TABLE IF NOT EXISTS chapter_characters (
    chapter_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    PRIMARY KEY (chapter_id, character_id),
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);
```

**Required functions:**
```python
def create_all_tables(connection: sqlite3.Connection) -> None:
    """Create all tables if they don't exist."""
    ...

def drop_all_tables(connection: sqlite3.Connection) -> None:
    """Drop all tables (for testing/reset)."""
    ...
```

**Acceptance Criteria:**
- [ ] All 5 tables defined with correct columns
- [ ] Foreign key relationships correct
- [ ] create_all_tables() works without error
- [ ] Tables persist after closing connection

**After completing:** Update PROJECT_STATE.md - mark 1.3 complete, set current task to 1.4

---

### Task 1.4 - Model Classes with CRUD

**Objective:** Create Python model classes that wrap database operations.

**Create files:**
- `/fast/BlueWriter/models/project.py`
- `/fast/BlueWriter/models/story.py`
- `/fast/BlueWriter/models/chapter.py`
- `/fast/BlueWriter/models/character.py`

**Base pattern for all models:**


```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import sqlite3

@dataclass
class Project:
    """Represents a writing project (series or standalone)."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, conn: sqlite3.Connection, name: str, description: str = "") -> "Project":
        """Insert new project and return instance."""
        ...
    
    @classmethod
    def get_by_id(cls, conn: sqlite3.Connection, project_id: int) -> Optional["Project"]:
        """Retrieve project by ID."""
        ...
    
    @classmethod
    def get_all(cls, conn: sqlite3.Connection) -> List["Project"]:
        """Retrieve all projects."""
        ...
    
    def update(self, conn: sqlite3.Connection) -> None:
        """Update project in database."""
        ...
    
    def delete(self, conn: sqlite3.Connection) -> None:
        """Delete project from database."""
        ...
```

**Implement similar patterns for:**
- Story (with project_id foreign key)
- Chapter (with story_id foreign key, includes board_x, board_y, color)
- Character (with project_id foreign key)

**Chapter model must include:**
- board_x: float - X position on timeline canvas
- board_y: float - Y position on timeline canvas  
- color: str - Hex color code for sticky note
- summary: str - Short 2-3 sentence summary shown on sticky
- content: str - Full chapter text (rich text HTML)

**Update models/__init__.py:**
```python
from .project import Project
from .story import Story
from .chapter import Chapter
from .character import Character

__all__ = ["Project", "Story", "Chapter", "Character"]
```

**Acceptance Criteria:**
- [ ] All 4 model classes implemented
- [ ] CRUD operations work for each model
- [ ] Foreign key relationships enforced
- [ ] Can create Project → Story → Chapter hierarchy
- [ ] models/__init__.py exports all classes

**After completing:** Update PROJECT_STATE.md - mark 1.4 complete, set current task to 2.1

---

## PHASE 2: APPLICATION SHELL

### Task 2.1 - Main Window with Menu Bar

**Objective:** Create the main application window with menu structure.

**Create files:**
- `/fast/BlueWriter/main.py`
- `/fast/BlueWriter/views/main_window.py`

**main.py structure:**
```python
"""BlueWriter - Fiction Writing Aid"""
import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("BlueWriter")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**MainWindow requirements:**
- Window title: "BlueWriter"
- Minimum size: 1200x800
- Menu bar with:
  - File menu: New Project, Open Project, Recent Projects >, Save, Exit
  - Edit menu: Undo, Redo, Cut, Copy, Paste
  - View menu: Zoom In, Zoom Out, Reset Zoom
  - Help menu: About
- Central widget placeholder (will be replaced with timeline canvas)
- Status bar showing "Ready"

**Acceptance Criteria:**
- [ ] Application launches without error: `python main.py`
- [ ] Window appears with correct title and size
- [ ] All menus visible and clickable (actions can be empty)
- [ ] Status bar shows "Ready"
- [ ] Window closes cleanly

**After completing:** Update PROJECT_STATE.md - mark 2.1 complete, set current task to 2.2

---

### Task 2.2 - Project Browser Dialog

**Objective:** Create dialog for creating/opening projects.

**Create file:** `/fast/BlueWriter/views/project_browser.py`

**Dialog requirements:**
- Modal dialog launched from File > New Project or File > Open Project
- Two tabs or sections:
  1. "New Project" - Name field, Description field, Create button
  2. "Open Project" - List of existing projects from database, Open button
- Recent projects shown in "Open Project" section
- Double-click project to open

**Class structure:**
```python
class ProjectBrowserDialog(QDialog):
    """Dialog for creating and opening projects."""
    
    project_selected = Signal(int)  # Emits project ID when selected
    
    def __init__(self, parent=None) -> None:
        ...
    
    def create_new_project(self) -> None:
        """Handle new project creation."""
        ...
    
    def open_selected_project(self) -> None:
        """Handle opening selected project."""
        ...
    
    def refresh_project_list(self) -> None:
        """Reload projects from database."""
        ...
```

**Acceptance Criteria:**
- [ ] Dialog opens from File menu
- [ ] Can create new project (saves to database)
- [ ] Existing projects listed
- [ ] Can select and open a project
- [ ] Dialog closes after selection

**After completing:** Update PROJECT_STATE.md - mark 2.2 complete, set current task to 2.3

---

### Task 2.3 - Story Management UI

**Objective:** UI for managing stories within a project.

**Create file:** `/fast/BlueWriter/views/story_selector.py`

**Requirements:**
- Sidebar or dropdown showing stories in current project
- "New Story" button
- Story properties: title, synopsis
- Selecting a story loads its chapters onto the timeline canvas

**Acceptance Criteria:**
- [ ] Can see list of stories in project
- [ ] Can create new story
- [ ] Can select story to view
- [ ] Selection triggers signal for canvas to load chapters

**After completing:** Update PROJECT_STATE.md - mark 2.3 complete, set current task to 3.1

---

## PHASE 3: TIMELINE CANVAS


### Task 3.1 - Canvas with Sine Wave Background

**Objective:** Create the main timeline canvas with visual sine wave guide.

**Create file:** `/fast/BlueWriter/views/timeline_canvas.py`

**Requirements:**
- QGraphicsView + QGraphicsScene based canvas
- Sine wave drawn as subtle background guide (not obtrusive)
- Wave parameters:
  - Amplitude: ~100 pixels (adjustable)
  - Wavelength: ~400 pixels (one full cycle)
  - Color: Light gray or subtle blue (#E0E8F0)
  - Line style: Dashed or dotted
- Canvas should be large (virtual size ~4000x2000 pixels)
- Background color: Light cream or white (#FAFAFA)

**Class structure:**
```python
class TimelineCanvas(QGraphicsView):
    """Main canvas for arranging chapter sticky notes."""
    
    def __init__(self, parent=None) -> None:
        ...
    
    def draw_sine_wave(self) -> None:
        """Draw the background sine wave guide."""
        ...
    
    def set_wave_parameters(self, amplitude: float, wavelength: float) -> None:
        """Adjust sine wave appearance."""
        ...
```

**Sine wave implementation hint:**
```python
import math
# Draw as QGraphicsPathItem
path = QPainterPath()
path.moveTo(0, center_y)
for x in range(0, canvas_width, 5):
    y = center_y + amplitude * math.sin(2 * math.pi * x / wavelength)
    path.lineTo(x, y)
```

**Acceptance Criteria:**
- [ ] Canvas displays in main window
- [ ] Sine wave visible as background guide
- [ ] Canvas scrollable if content exceeds view
- [ ] Performance is smooth (no lag on scroll)

**After completing:** Update PROJECT_STATE.md - mark 3.1 complete, set current task to 3.2

---

### Task 3.2 - Sticky Note Widget

**Objective:** Create the visual sticky note that represents a chapter.

**Create file:** `/fast/BlueWriter/views/sticky_note.py`

**Visual design:**
- Size: ~150x100 pixels (width x height)
- Background: Customizable color (default yellow #FFFF88)
- Border: Subtle shadow or 1px darker border
- Content: Chapter title (bold) + summary (2-3 lines, truncated with ...)
- Visual indicator if chapter has content vs. empty

**Class structure:**
```python
class StickyNoteItem(QGraphicsWidget):
    """Visual representation of a chapter on the timeline."""
    
    double_clicked = Signal(int)  # Emits chapter ID
    position_changed = Signal(int, float, float)  # chapter_id, x, y
    
    def __init__(self, chapter: Chapter, parent=None) -> None:
        ...
    
    def update_from_chapter(self, chapter: Chapter) -> None:
        """Update display from chapter data."""
        ...
    
    def set_color(self, color: str) -> None:
        """Change sticky note color."""
        ...
    
    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click to open editor."""
        ...
```

**Acceptance Criteria:**
- [ ] Sticky note renders correctly on canvas
- [ ] Title and summary displayed
- [ ] Color is customizable
- [ ] Double-click emits signal with chapter ID
- [ ] Visually distinct from background

**After completing:** Update PROJECT_STATE.md - mark 3.2 complete, set current task to 3.3

---

### Task 3.3 - Drag and Drop Positioning

**Objective:** Make sticky notes draggable on the canvas.

**Create file:** `/fast/BlueWriter/controllers/canvas_controller.py`

**Requirements:**
- Sticky notes can be dragged to any position
- Position saved to database when drag ends
- Visual feedback during drag (slight lift/shadow)
- Grid snap optional (can implement later)
- Multiple selection for group move (shift+click)

**Implementation in StickyNoteItem:**
```python
# Enable dragging
self.setFlag(QGraphicsItem.ItemIsMovable, True)
self.setFlag(QGraphicsItem.ItemIsSelectable, True)
self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

def itemChange(self, change, value):
    if change == QGraphicsItem.ItemPositionHasChanged:
        # Emit signal to save new position
        self.position_changed.emit(self.chapter_id, value.x(), value.y())
    return super().itemChange(change, value)
```

**CanvasController responsibilities:**
- Listen for position_changed signals
- Batch save positions (debounce rapid movements)
- Load chapters and create sticky notes for a story
- Handle selection state

**Acceptance Criteria:**
- [ ] Sticky notes can be dragged
- [ ] Position persists after restart
- [ ] Multiple notes can be selected and moved together
- [ ] No performance issues with 50+ notes

**After completing:** Update PROJECT_STATE.md - mark 3.3 complete, set current task to 3.4

---

### Task 3.4 - Pan and Zoom Controls

**Objective:** Allow user to navigate large canvases.

**Update file:** `/fast/BlueWriter/views/timeline_canvas.py`

**Requirements:**
- Mouse wheel: Zoom in/out (centered on cursor)
- Middle mouse drag OR Space+Left drag: Pan canvas
- View menu actions: Zoom In, Zoom Out, Reset Zoom (100%)
- Zoom range: 25% to 200%
- Smooth zoom animation (optional but nice)

**Key implementation:**
```python
def wheelEvent(self, event):
    """Handle zoom with mouse wheel."""
    zoom_factor = 1.15
    if event.angleDelta().y() > 0:
        self.scale(zoom_factor, zoom_factor)
    else:
        self.scale(1/zoom_factor, 1/zoom_factor)

def keyPressEvent(self, event):
    if event.key() == Qt.Key_Space:
        self.setDragMode(QGraphicsView.ScrollHandDrag)

def keyReleaseEvent(self, event):
    if event.key() == Qt.Key_Space:
        self.setDragMode(QGraphicsView.NoDrag)
```

**Acceptance Criteria:**
- [ ] Mouse wheel zooms in/out
- [ ] Can pan canvas with middle mouse or space+drag
- [ ] View menu zoom actions work
- [ ] Zoom level shown in status bar
- [ ] Reset zoom returns to 100%

**After completing:** Update PROJECT_STATE.md - mark 3.4 complete, set current task to 4.1

---

## PHASE 4: CHAPTER EDITING


### Task 4.1 - Chapter Editor Dialog

**Objective:** Create the dialog for editing chapter content.

**Create file:** `/fast/BlueWriter/views/chapter_editor.py`

**Requirements:**
- Modal or non-modal dialog (user preference, start with non-modal)
- Fields:
  - Title (QLineEdit)
  - Summary (QTextEdit, 2-3 lines max display)
  - Content (QTextEdit, main editor area)
  - Color picker for sticky note color
- Minimum size: 800x600
- Resizable

**Class structure:**
```python
class ChapterEditorDialog(QDialog):
    """Dialog for editing chapter details and content."""
    
    chapter_updated = Signal(Chapter)  # Emits when saved
    
    def __init__(self, chapter: Chapter, parent=None) -> None:
        ...
    
    def load_chapter(self, chapter: Chapter) -> None:
        """Populate fields from chapter."""
        ...
    
    def save_chapter(self) -> None:
        """Save changes to database."""
        ...
    
    def pick_color(self) -> None:
        """Open color picker dialog."""
        ...
```

**Acceptance Criteria:**
- [ ] Dialog opens on sticky note double-click
- [ ] All fields populated from chapter data
- [ ] Can edit and save changes
- [ ] Sticky note updates after save
- [ ] Color picker works

**After completing:** Update PROJECT_STATE.md - mark 4.1 complete, set current task to 4.2

---

### Task 4.2 - Formatting Toolbar

**Objective:** Add basic rich text formatting to chapter editor.

**Update file:** `/fast/BlueWriter/views/chapter_editor.py`

**Create file:** `/fast/BlueWriter/utils/text_formatting.py`

**Toolbar buttons:**
- Bold (Ctrl+B)
- Italic (Ctrl+I)
- Underline (Ctrl+U)
- Heading 1, Heading 2
- Bullet list
- Numbered list
- Separator/horizontal rule

**Implementation:**
- Use QTextEdit's built-in rich text support
- Content stored as HTML in database
- Toolbar actions use QTextEdit's setFontWeight(), setFontItalic(), etc.

**Example:**
```python
def toggle_bold(self):
    fmt = self.content_edit.currentCharFormat()
    weight = QFont.Normal if fmt.fontWeight() == QFont.Bold else QFont.Bold
    fmt.setFontWeight(weight)
    self.content_edit.mergeCurrentCharFormat(fmt)
```

**Acceptance Criteria:**
- [ ] Toolbar visible above content editor
- [ ] Bold/Italic/Underline toggle correctly
- [ ] Headers change text size
- [ ] Lists work
- [ ] Formatting preserved on save/load

**After completing:** Update PROJECT_STATE.md - mark 4.2 complete, set current task to 4.3

---

### Task 4.3 - Auto-save System

**Objective:** Implement automatic saving with dirty state tracking.

**Create file:** `/fast/BlueWriter/controllers/story_controller.py`

**Requirements:**
- Track "dirty" state (unsaved changes exist)
- Auto-save every 60 seconds if dirty
- Visual indicator of unsaved changes (asterisk in title bar)
- Prompt to save on close if dirty
- Undo/redo stack (QUndoStack)

**StoryController responsibilities:**
```python
class StoryController(QObject):
    """Manages story state and persistence."""
    
    dirty_changed = Signal(bool)  # True when unsaved changes
    
    def __init__(self, db_manager: DatabaseManager) -> None:
        ...
    
    def mark_dirty(self) -> None:
        """Mark current story as having unsaved changes."""
        ...
    
    def save(self) -> None:
        """Save all changes to database."""
        ...
    
    def setup_autosave(self, interval_seconds: int = 60) -> None:
        """Start auto-save timer."""
        ...
```

**Acceptance Criteria:**
- [ ] Dirty state tracked correctly
- [ ] Window title shows * when dirty
- [ ] Auto-save triggers after 60 seconds of inactivity
- [ ] Close prompt appears if unsaved changes
- [ ] Undo/redo works for text changes

**After completing:** Update PROJECT_STATE.md - mark 4.3 complete, set current task to 5.1

---

## PHASE 5: INTEGRATION & POLISH

### Task 5.1 - Full Integration Testing

**Objective:** Wire all components together and fix integration issues.

**Test workflow:**
1. Launch application
2. Create new project "Test Novel"
3. Create story "Book One"
4. Add 5+ chapters with titles and content
5. Arrange chapters on timeline
6. Close and reopen - verify all data persists
7. Edit a chapter, verify auto-save
8. Test with 20+ chapters for performance

**Fix any issues discovered during testing.**

**Acceptance Criteria:**
- [ ] Complete workflow works end-to-end
- [ ] Data persists correctly
- [ ] No crashes or errors
- [ ] Performance acceptable with 20+ chapters
- [ ] All signals/slots connected properly

**After completing:** Update PROJECT_STATE.md - mark 5.1 complete, set current task to 5.2

---

### Task 5.2 - QSS Styling

**Objective:** Create cohesive visual styling.

**Create file:** `/fast/BlueWriter/resources/styles.qss`

**Style goals:**
- Clean, professional appearance
- Easy on the eyes for long writing sessions
- Consistent spacing and typography
- Sticky notes should feel like paper

**Elements to style:**
- Main window background
- Menu bar and menus
- Buttons (normal, hover, pressed states)
- Text inputs and editors
- Dialogs
- Sticky notes on canvas
- Scrollbars
- Status bar

**Load stylesheet in main.py:**
```python
style_path = Path(__file__).parent / "resources" / "styles.qss"
if style_path.exists():
    app.setStyleSheet(style_path.read_text())
```

**Acceptance Criteria:**
- [ ] Stylesheet loads without errors
- [ ] All major UI elements styled
- [ ] Visual consistency throughout app
- [ ] No broken layouts from styling

**After completing:** Update PROJECT_STATE.md - mark 5.2 complete, set current task to 5.3

---

### Task 5.3 - Keyboard Shortcuts and UX Polish

**Objective:** Final usability improvements.

**Keyboard shortcuts:**
| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+O | Open Project |
| Ctrl+S | Save |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+Shift+N | New Chapter |
| Delete | Delete selected chapter(s) |
| F2 | Rename selected chapter |
| Escape | Deselect all / Close dialog |
| +/- | Zoom in/out |
| Ctrl+0 | Reset zoom |

**UX improvements:**
- Tab order in dialogs
- Focus indicators
- Tooltips on toolbar buttons
- Confirmation dialogs for destructive actions
- Empty state messaging ("Create your first chapter!")
- Loading indicator for database operations

**Acceptance Criteria:**
- [ ] All shortcuts work
- [ ] Tooltips on all buttons
- [ ] Confirmation on delete
- [ ] Tab order logical
- [ ] Empty states handled gracefully

**After completing:** Update PROJECT_STATE.md - mark 5.3 complete, PROJECT COMPLETE!

---

## POST-BETA FEATURES (Future Reference)

These are NOT part of the current task list. Do not implement unless specifically instructed.

- Export to Markdown/HTML/DOCX
- Character management UI
- Emotional intensity scoring (MCP integration)
- Multiple story views (outline, timeline, index cards)
- Search across all chapters
- Word count tracking and goals
- Backup/restore functionality
- Theme switching (light/dark mode)
- Mobile companion app

---

## TROUBLESHOOTING

### Common Issues

**"ModuleNotFoundError: No module named 'PySide6'"**
→ Run: `pip install -r requirements.txt`

**"Cannot connect to database"**
→ Check that `/fast/BlueWriter/data/` directory exists and is writable

**"Sticky notes not appearing"**
→ Verify chapters have valid story_id and scene is set on QGraphicsView

**Application hangs on startup**
→ Check for infinite loops in signal/slot connections

### Getting Unstuck

If you're looping or confused:
1. Stop and read PROJECT_STATE.md
2. Identify exactly which task you're on
3. Read ONLY that task's specification
4. Complete that task before moving on
5. Update PROJECT_STATE.md before next task
