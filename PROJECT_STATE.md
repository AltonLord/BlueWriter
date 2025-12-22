# PROJECT STATE - BlueWriter

**Last Updated:** Not started
**Current Phase:** 1 - Foundation
**Overall Status:** NOT STARTED

---

## CURRENT TASK

**Task ID:** 5.4
**Title:** Tutorial creation
**Status:** COMPLETE
**Assigned Files:** 
- TUTORIAL.md

**Instructions:** See TASKS.md for detailed specifications.

---

## COMPLETED TASKS

*None yet*

---

## PENDING TASKS

### Phase 1: Foundation
- [x] 1.1 - Create directory structure and requirements.txt
- [x] 1.2 - Database connection manager
- [x] 1.3 - Schema definition
- [x] 1.4 - Model classes with CRUD

### Phase 2: Application Shell
- [x] 2.1 - Main window with menu bar
- [x] 2.2 - Project browser dialog
- [x] 2.3 - Story management UI

### Phase 3: Timeline Canvas
- [x] 3.1 - Canvas with sine wave background
- [x] 3.2 - Sticky note widget
- [x] 3.3 - Drag and drop positioning
- [x] 3.4 - Pan/zoom controls

### Phase 4: Chapter Editing
- [x] 4.1 - Chapter editor dialog
- [x] 4.2 - Formatting toolbar
- [x] 4.3 - Auto-save system

### Phase 5: Integration & Polish
- [x] 5.1 - Full integration testing
- [x] 5.2 - QSS styling
- [x] 5.3 - Keyboard shortcuts and UX

---

## BLOCKING ISSUES

*None currently*

---

## KEY DECISIONS

| Decision | Chosen | Rationale | Task |
|----------|--------|-----------|------|
| GUI Framework | PySide6 | Official Qt binding, LGPL license, cross-platform | Pre-project |
| Database | SQLite | Local storage, no server, supports undo history | Pre-project |
| Language | Python 3.10+ | Fast iteration, cross-platform, eventual mobile | Pre-project |
| Data Model | Project → Story → Chapter hierarchy | Supports series with shared characters | Pre-project |

---

## PROJECT CONSTRAINTS

### MUST USE
- Python 3.10 or higher
- PySide6 for all GUI components
- SQLite for data storage
- Local file system only (offline-first)
- Virtual environment at `/fast/BlueWriter/venv/`
  - Use `/fast/BlueWriter/venv/bin/python` to run Python
  - Use `/fast/BlueWriter/venv/bin/pip` to install packages
  - Example: `/fast/BlueWriter/venv/bin/pip install -r requirements.txt`
- Virtual environment at `/fast/BlueWriter/venv/`
  - Use `/fast/BlueWriter/venv/bin/python` to run Python
  - Use `/fast/BlueWriter/venv/bin/pip` to install packages
  - Example: `/fast/BlueWriter/venv/bin/pip install -r requirements.txt`

### DO NOT USE
- JavaScript or any web technologies
- PyQt5 (use PySide6 instead)
- External web APIs or services
- Electron, Tauri, or browser-based solutions
- Online databases or cloud storage

### CODING STANDARDS
- Type hints on all function signatures
- Docstrings on all classes and public methods
- Snake_case for files, functions, variables
- PascalCase for class names
- Maximum line length: 100 characters

---

## FILE MANIFEST

*Updated as files are created*

```
/fast/BlueWriter/
├── PROJECT_STATE.md    ← This file
├── TASKS.md            ← Task specifications
└── (other files added as created)
```

---

## SESSION LOG

*Record each work session below*

### Session Template
```
**Date:** YYYY-MM-DD
**Task:** X.X - Task Name
**Actions Taken:**
- Action 1
- Action 2
**Files Created/Modified:**
- file1.py (created)
- file2.py (modified)
**Issues Encountered:**
- None / Description
**Next Steps:**
- What to do next session
```
