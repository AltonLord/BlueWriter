"""
Main window for BlueWriter application.
Integrates all UI components: sidebar, timeline canvas, and dialogs.
"""
from PySide6.QtWidgets import (
    QMainWindow, QStatusBar, QToolBar, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QLabel, QPushButton, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from views.timeline_canvas import TimelineCanvas
from views.story_panel import StoryPanelWidget
from views.story_metadata_dialog import StoryMetadataDialog
from views.project_browser import ProjectBrowserDialog
from views.chapter_editor_dock import ChapterEditorDock
from views.sticky_note import StickyNote
from views.encyclopedia_widget import EncyclopediaWidget
from views.dictionary_editor import DictionaryEditorDialog
from views.publish_dialog import PublishDialog, UnpublishDialog
from views.export_dialog import ExportDialog
from views.import_dialog import ImportDialog
from database.connection import DatabaseManager, get_default_db_path
from database.schema import create_all_tables
from models.project import Project
from models.story import Story
from models.chapter import Chapter
from services import ServiceContainer
from adapters.qt_adapter import QtEventAdapter


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("BlueWriter")
        self.setMinimumSize(QSize(1200, 800))

        # Initialize database
        self.db_manager = DatabaseManager(get_default_db_path())
        with self.db_manager as conn:
            create_all_tables(conn)

        # Initialize service layer and API
        self._init_services()

        # Current state
        self.current_project_id = None
        self.current_story_id = None
        self.sticky_notes = []  # Track sticky note widgets
        self.open_editors = {}  # Track open chapter editors: {chapter_id: ChapterEditorDock}

        # Create UI components
        self.setup_ui()
        self.create_menus()
        self.create_toolbars()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Create or open a project to begin")

    def _init_services(self) -> None:
        """Initialize the service layer, event adapter, and API server."""
        db_path = str(get_default_db_path())

        # Create service container with all services
        self.services = ServiceContainer(db_path)

        # Create Qt event adapter (bridges events to Qt signals)
        self.event_adapter = QtEventAdapter(self.services.event_bus, self)

        # Connect adapter signals to handlers
        self._connect_event_signals()

        # Start REST API server in background thread
        try:
            self.services.start_api_server(port=5000)
            print(f"BlueWriter API running on {self.services.get_api_url()}")
        except Exception as e:
            print(f"Warning: Could not start API server: {e}")

    def _connect_event_signals(self) -> None:
        """Connect Qt event adapter signals to UI update handlers."""
        # Story events - update story panel when stories change via MCP/API
        self.event_adapter.story_created.connect(self._on_service_story_created)
        self.event_adapter.story_deleted.connect(self._on_service_story_deleted)
        self.event_adapter.story_updated.connect(self._on_service_story_updated)

        # Chapter events - update canvas when chapters change
        self.event_adapter.chapter_created.connect(self._on_service_chapter_created)
        self.event_adapter.chapter_deleted.connect(self._on_service_chapter_deleted)
        self.event_adapter.chapter_moved.connect(self._on_service_chapter_moved)
        self.event_adapter.chapter_color_changed.connect(self._on_service_chapter_color_changed)

    def _on_service_chapter_created(
        self, chapter_id: int, story_id: int, title: str,
        board_x: int, board_y: int, color: str
    ) -> None:
        """Handle chapter created by service (e.g., from API/MCP).

        On the unified canvas, any new chapter for the current project should appear.
        """
        if self.current_project_id:
            with self.db_manager as conn:
                chapter = Chapter.get_by_id(conn, chapter_id)
                if chapter and chapter.project_id == self.current_project_id:
                    self.add_sticky_note(chapter)

    def _on_service_chapter_deleted(self, chapter_id: int, story_id: int) -> None:
        """Handle chapter deleted by service."""
        # Find and remove the sticky note regardless of story
        for note in self.sticky_notes[:]:
            if note.chapter.id == chapter_id:
                note.setParent(None)
                note.deleteLater()
                self.sticky_notes.remove(note)
                break
        # Close editor if open
        if chapter_id in self.open_editors:
            self.open_editors[chapter_id].close()

    def _on_service_chapter_moved(
        self, chapter_id: int, old_x: int, old_y: int,
        new_x: int, new_y: int
    ) -> None:
        """Handle chapter moved by service."""
        for note in self.sticky_notes:
            if note.chapter.id == chapter_id:
                note.chapter.board_x = new_x
                note.chapter.board_y = new_y
                screen_x, screen_y = self.canvas.canvas_to_screen(new_x, new_y)
                note.move(int(screen_x), int(screen_y))
                break

    def _on_service_chapter_color_changed(
        self, chapter_id: int, old_color: str, new_color: str
    ) -> None:
        """Handle chapter color changed by service."""
        for note in self.sticky_notes:
            if note.chapter.id == chapter_id:
                note.chapter.color = new_color
                note.update_color()
                break

    # === Story Event Handlers (from API/MCP) ===

    def _on_service_story_created(self, story_id: int, project_id: int, title: str) -> None:
        """Handle story created via MCP/API — add card to story panel and overlay to canvas."""
        if project_id != self.current_project_id or self.story_panel is None:
            return
        try:
            story_dto = self.services.story_service.get_story(story_id)
            self.story_panel.add_story(story_dto)
            self.canvas.set_stories(self.canvas._stories + [story_dto])
            self.status_bar.showMessage(f"Story '{title}' created via MCP")
        except Exception as e:
            print(f"Error handling story_created event: {e}")

    def _on_service_story_deleted(self, story_id: int) -> None:
        """Handle story deleted via MCP/API — remove card and canvas overlay."""
        if self.story_panel is None:
            return
        self.story_panel.remove_story(story_id)
        self.canvas._stories = [s for s in self.canvas._stories if s.id != story_id]
        self.canvas.update()

    def _on_service_story_updated(self, story_id: int, fields_changed: list) -> None:
        """Handle story updated via MCP/API — refresh the story panel card."""
        if self.story_panel is None:
            return
        try:
            story_dto = self.services.story_service.get_story(story_id)
            # Update in canvas stories list
            self.canvas._stories = [
                story_dto if s.id == story_id else s
                for s in self.canvas._stories
            ]
            # Reload the panel to reflect changes (simple approach)
            self._reload_story_panel()
        except Exception as e:
            print(f"Error handling story_updated event: {e}")

    def _reload_story_panel(self) -> None:
        """Reload story panel cards from current canvas stories."""
        if self.story_panel and self.current_project_id:
            self.story_panel.load_stories(self.canvas._stories)

    def setup_ui(self) -> None:
        """Set up the main UI layout with sidebar and canvas."""
        # Main container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for sidebar and canvas
        self.splitter = QSplitter(Qt.Horizontal)

        # Left sidebar (placeholder until project is loaded)
        self.sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setContentsMargins(5, 5, 5, 5)

        # Welcome message in sidebar
        self.welcome_label = QLabel("Welcome to BlueWriter!\n\nUse File \u2192 New Project\nor File \u2192 Open Project\nto get started.")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setWordWrap(True)
        self.sidebar_layout.addWidget(self.welcome_label)

        self.sidebar_container.setMinimumWidth(200)
        self.sidebar_container.setMaximumWidth(350)

        # Story panel (will be created when project loads)
        self.story_panel = None

        # Encyclopedia widget (will be created when project loads)
        self.encyclopedia_widget = None

        # Right side: Timeline canvas
        self.canvas = TimelineCanvas()
        self.canvas.new_chapter_requested.connect(self.add_chapter_at_position)
        self.canvas.story_outline_updated.connect(self._on_story_outline_updated)

        # Add to splitter
        self.splitter.addWidget(self.sidebar_container)
        self.splitter.addWidget(self.canvas)
        self.splitter.setSizes([250, 950])

        main_layout.addWidget(self.splitter)

    def create_menus(self) -> None:
        """Create all menu items with connected actions."""
        menubar = self.menuBar()

        # === File menu ===
        file_menu = menubar.addMenu("&File")

        new_project_action = QAction("&New Project", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction("&Open Project", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        import_project_action = QAction("&Import Project...", self)
        import_project_action.setShortcut("Ctrl+I")
        import_project_action.triggered.connect(self.import_project)
        file_menu.addAction(import_project_action)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Publish submenu
        publish_menu = file_menu.addMenu("&Publish")

        self.publish_story_action = QAction("Publish Current Story...", self)
        self.publish_story_action.triggered.connect(self.publish_story)
        self.publish_story_action.setEnabled(False)
        publish_menu.addAction(self.publish_story_action)

        self.unpublish_story_action = QAction("Unpublish Current Story...", self)
        self.unpublish_story_action.triggered.connect(self.unpublish_story)
        self.unpublish_story_action.setEnabled(False)
        publish_menu.addAction(self.unpublish_story_action)

        # Export
        self.export_action = QAction("&Export Project...", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self.export_project)
        self.export_action.setEnabled(False)
        file_menu.addAction(self.export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # === Edit menu ===
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        dictionary_action = QAction("Custom &Dictionary...", self)
        dictionary_action.triggered.connect(self.open_dictionary_editor)
        edit_menu.addAction(dictionary_action)

        # === View menu ===
        view_menu = menubar.addMenu("&View")

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("+")
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("-")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        # === Help menu ===
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbars(self) -> None:
        """Create toolbars with chapter actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # New Chapter button (always enabled when project is loaded)
        self.new_chapter_action = QAction("New Chapter", self)
        self.new_chapter_action.setShortcut("Ctrl+Shift+N")
        self.new_chapter_action.triggered.connect(self.add_chapter)
        self.new_chapter_action.setEnabled(False)
        toolbar.addAction(self.new_chapter_action)

        toolbar.addSeparator()

        # Refresh button
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_canvas)
        toolbar.addAction(refresh_action)

    def new_project(self) -> None:
        """Open dialog to create a new project."""
        dialog = ProjectBrowserDialog(self)
        dialog.project_selected.connect(self.load_project)
        dialog.exec()

    def open_project(self) -> None:
        """Open dialog to select an existing project."""
        dialog = ProjectBrowserDialog(self)
        dialog.project_selected.connect(self.load_project)
        dialog.exec()

    def import_project(self, checked: bool = False) -> None:
        """Open dialog to import a project from ZIP archive."""
        dialog = ImportDialog(self)
        if dialog.exec():
            project_id = dialog.get_imported_project_id()
            if project_id:
                self.load_project(project_id)

    def load_project(self, project_id: int) -> None:
        """Load a project: set up story panel, encyclopedia, and unified canvas."""
        self.current_project_id = project_id
        self.current_story_id = None

        # Get project info for title
        with self.db_manager as conn:
            project = Project.get_by_id(conn, project_id)
            if project:
                self.setWindowTitle(f"BlueWriter - {project.name}")

        # Clear old sidebar content
        if self.story_panel:
            self.sidebar_layout.removeWidget(self.story_panel)
            self.story_panel.deleteLater()

        if self.encyclopedia_widget:
            self.sidebar_layout.removeWidget(self.encyclopedia_widget)
            self.encyclopedia_widget.deleteLater()

        # Hide welcome message
        self.welcome_label.hide()

        # Create story panel for this project (top of sidebar)
        self.story_panel = StoryPanelWidget(self)
        self.story_panel.story_created.connect(self._on_new_story_requested)
        self.story_panel.frame_story_requested.connect(self._on_frame_story)
        self.story_panel.outline_edit_requested.connect(self._on_outline_edit)
        self.story_panel.delete_requested.connect(self._on_delete_story)
        self.story_panel.edit_metadata_requested.connect(self._on_edit_story_metadata)
        self.sidebar_layout.insertWidget(0, self.story_panel)

        # Create encyclopedia widget (bottom of sidebar)
        self.encyclopedia_widget = EncyclopediaWidget(project_id, self)
        self.sidebar_layout.addWidget(self.encyclopedia_widget)

        # Enable actions
        self.export_action.setEnabled(True)
        self.new_chapter_action.setEnabled(True)

        # Load unified canvas with all chapters and stories
        self._load_unified_canvas()

        self.status_bar.showMessage(f"Project loaded.")

    def _load_unified_canvas(self) -> None:
        """Load all chapters and stories for the current project onto the canvas."""
        self.clear_canvas()

        if not self.current_project_id:
            return

        with self.db_manager as conn:
            # Load all stories
            stories = Story.get_by_project(conn, self.current_project_id)
            story_dtos = []
            for s in stories:
                from services.story_service import StoryDTO
                story_dtos.append(StoryDTO(
                    id=s.id, project_id=s.project_id, title=s.title,
                    synopsis=s.synopsis, sort_order=s.sort_order, status=s.status,
                    published_at=s.published_at, created_at=s.created_at,
                    updated_at=s.updated_at,
                    representation_type=s.representation_type,
                    bounding_data=s.bounding_data,
                    outline_color=s.outline_color,
                ))

            # Load all chapters for the project
            all_chapters = Chapter.get_by_project(conn, self.current_project_id)
            chapter_dtos = []
            for ch in all_chapters:
                from services.chapter_service import ChapterDTO
                chapter_dtos.append(ChapterDTO(
                    id=ch.id, story_id=ch.story_id, title=ch.title,
                    summary=ch.summary, content=ch.content,
                    board_x=ch.board_x, board_y=ch.board_y,
                    sort_order=ch.sort_order, color=ch.color,
                    created_at=ch.created_at, updated_at=ch.updated_at,
                    project_id=ch.project_id,
                ))

        # Update story panel
        self.story_panel.load_stories(story_dtos)

        # Update canvas with story overlays
        self.canvas.load_project(self.current_project_id, chapter_dtos, story_dtos)

        # Add sticky notes for all chapters
        with self.db_manager as conn:
            for ch in all_chapters:
                self.add_sticky_note(ch)

    # === Story Panel Signal Handlers ===

    def _on_new_story_requested(self, _signal_value: int) -> None:
        """Handle '+ New Story' button click."""
        title, ok = QInputDialog.getText(self, "New Story", "Story title:")
        if ok and title.strip():
            try:
                story_dto = self.services.story_service.create_story(
                    project_id=self.current_project_id,
                    title=title.strip(),
                )
                self.story_panel.add_story(story_dto)
                self.canvas.set_stories(
                    self.canvas._stories + [story_dto]
                )
                self.status_bar.showMessage(f"Story '{title.strip()}' created")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _on_frame_story(self, story_id: int) -> None:
        """Handle double-click on story card: zoom canvas to frame story's chapters."""
        self.current_story_id = story_id

        # Get story chapters
        story_chapters = [ch for ch in self.canvas._chapters if ch.story_id == story_id]

        # Find the story DTO
        story_dto = None
        for s in self.canvas._stories:
            if s.id == story_id:
                story_dto = s
                break

        if story_dto and story_chapters:
            self.canvas.frame_story(story_dto, story_chapters)
            self.status_bar.showMessage(f"Viewing: {story_dto.title}")
        elif story_dto:
            self.status_bar.showMessage(f"Story '{story_dto.title}' has no chapters yet")

        # Update publish action states
        with self.db_manager as conn:
            story = Story.get_by_id(conn, story_id)
            if story:
                self.publish_story_action.setEnabled(not story.is_locked)
                self.unpublish_story_action.setEnabled(story.is_locked)

    def _on_outline_edit(self, story_id: int) -> None:
        """Handle 'Edit Outline' button on story card."""
        self.canvas.enter_outline_edit_mode(story_id)
        self.status_bar.showMessage("Outline edit mode - press Escape to exit")

    def _on_story_outline_updated(self, story_id: int, bounding_data: str) -> None:
        """Handle story outline updated from canvas."""
        try:
            self.services.story_service.update_story_outline(
                story_id=story_id,
                bounding_data=bounding_data,
            )
        except Exception as e:
            print(f"Error saving story outline: {e}")

    def _on_delete_story(self, story_id: int) -> None:
        """Handle 'Delete Story' from story card context menu."""
        # Confirm deletion
        with self.db_manager as conn:
            story = Story.get_by_id(conn, story_id)

        if not story:
            return

        reply = QMessageBox.question(
            self, "Delete Story",
            f"Delete story '{story.title}'?\n\n"
            "The story grouping will be removed, but all chapters will remain on the canvas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.services.story_service.delete_story(story_id)
                self.story_panel.remove_story(story_id)
                # Refresh canvas overlays
                self.canvas._stories = [s for s in self.canvas._stories if s.id != story_id]
                self.canvas.update()
                self.status_bar.showMessage(f"Story '{story.title}' deleted. Chapters kept.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _on_edit_story_metadata(self, story_id: int) -> None:
        """Handle 'Edit Metadata' from story card context menu."""
        # Find the story DTO
        story_dto = None
        for s in self.canvas._stories:
            if s.id == story_id:
                story_dto = s
                break

        if not story_dto:
            return

        dialog = StoryMetadataDialog(story_dto, self)
        if dialog.exec():
            try:
                # Update story metadata
                self.services.story_service.update_story(
                    story_id=story_id,
                    title=dialog.get_title(),
                    synopsis=dialog.get_synopsis(),
                )
                # Update outline properties
                self.services.story_service.update_story_outline(
                    story_id=story_id,
                    representation_type=dialog.get_representation_type(),
                    outline_color=dialog.get_outline_color(),
                )
                # Reload the canvas to reflect changes
                self._load_unified_canvas()
                self.status_bar.showMessage("Story metadata updated")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # === Chapter Actions ===

    def add_chapter(self) -> None:
        """Create a new chapter and add it to the canvas.

        Chapters can be created as orphans (no story) or attached to current_story_id.
        """
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project",
                              "Please open a project first.")
            return

        with self.db_manager as conn:
            # Get count for default position
            all_chapters = Chapter.get_by_project(conn, self.current_project_id)
            x_pos = 100 + (len(all_chapters) * 180)
            y_pos = 200

            chapter = Chapter.create(
                conn,
                story_id=self.current_story_id,  # May be None (orphan)
                title=f"Chapter {len(all_chapters) + 1}",
                summary="Click to add summary...",
                content="",
                project_id=self.current_project_id,
            )
            chapter.board_x = x_pos
            chapter.board_y = y_pos
            chapter.update(conn)

            self.add_sticky_note(chapter)
            self.open_chapter_editor(chapter)

        self.status_bar.showMessage("New chapter created")

    def add_chapter_at_position(self, x: float, y: float) -> None:
        """Create a new chapter at specific canvas position (from right-click)."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project",
                              "Please open a project first.")
            return

        with self.db_manager as conn:
            all_chapters = Chapter.get_by_project(conn, self.current_project_id)

            chapter = Chapter.create(
                conn,
                story_id=self.current_story_id,  # May be None (orphan)
                title=f"Chapter {len(all_chapters) + 1}",
                summary="Click to add summary...",
                content="",
                project_id=self.current_project_id,
            )
            chapter.board_x = x
            chapter.board_y = y
            chapter.update(conn)

            self.add_sticky_note(chapter)
            self.open_chapter_editor(chapter)

        self.status_bar.showMessage("New chapter created")

    def add_sticky_note(self, chapter: Chapter) -> None:
        """Add a sticky note widget for a chapter."""
        note = StickyNote(chapter, parent=self.canvas)

        # Position using canvas coordinate transformation
        screen_x, screen_y = self.canvas.canvas_to_screen(chapter.board_x, chapter.board_y)
        note.move(int(screen_x), int(screen_y))

        note.double_clicked.connect(lambda: self.on_chapter_double_click(chapter.id))
        note.position_changed.connect(self.on_chapter_moved)
        note.show()
        self.sticky_notes.append(note)

    def on_chapter_double_click(self, chapter_id: int) -> None:
        """Open chapter editor when sticky note is double-clicked."""
        with self.db_manager as conn:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter and chapter.story_id:
                story = Story.get_by_id(conn, chapter.story_id)
                if story and story.is_locked:
                    QMessageBox.information(
                        self,
                        "Story Locked",
                        f"'{story.title}' is final published and locked.\n\n"
                        "Use File \u2192 Publish \u2192 Unpublish to unlock for editing."
                    )
                    return

        # Check if already open
        if chapter_id in self.open_editors:
            editor = self.open_editors[chapter_id]
            editor.show()
            editor.raise_()
            editor.setFocus()
            return

        if chapter:
            self.open_chapter_editor(chapter)

    def open_chapter_editor(self, chapter: Chapter) -> None:
        """Open a dockable chapter editor."""
        if chapter.id in self.open_editors:
            editor = self.open_editors[chapter.id]
            editor.show()
            editor.raise_()
            return

        editor = ChapterEditorDock(chapter, self)
        editor.chapter_saved.connect(self.on_chapter_saved)
        editor.chapter_closed.connect(self.on_editor_closed)

        self.addDockWidget(Qt.RightDockWidgetArea, editor)
        editor.setFloating(True)
        editor.resize(700, 500)

        self.open_editors[chapter.id] = editor

    def on_editor_closed(self, chapter_id: int) -> None:
        """Handle editor close - remove from tracking."""
        if chapter_id in self.open_editors:
            del self.open_editors[chapter_id]

    def on_chapter_saved(self, chapter: Chapter) -> None:
        """Handle chapter save - update sticky note display."""
        for note in self.sticky_notes:
            if note.chapter.id == chapter.id:
                note.update_from_chapter(chapter)
                screen_x, screen_y = self.canvas.canvas_to_screen(chapter.board_x, chapter.board_y)
                note.move(int(screen_x), int(screen_y))
                break
        self.status_bar.showMessage("Chapter saved")

    def on_chapter_moved(self, chapter_id: int, x: float, y: float) -> None:
        """Save chapter position when sticky note is moved."""
        with self.db_manager as conn:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter:
                chapter.board_x = x
                chapter.board_y = y
                chapter.update(conn)

    def clear_canvas(self) -> None:
        """Remove all sticky notes from canvas."""
        for note in self.sticky_notes:
            note.setParent(None)
            note.deleteLater()
        self.sticky_notes.clear()
        self.canvas.update()

    def save_project(self) -> None:
        """Save current project state."""
        self.status_bar.showMessage("Project saved")

    def refresh_canvas(self) -> None:
        """Reload all chapters and stories from database."""
        self._load_unified_canvas()
        self.status_bar.showMessage("Canvas refreshed")

    def open_dictionary_editor(self) -> None:
        """Open the custom dictionary editor dialog."""
        dialog = DictionaryEditorDialog(self)
        dialog.exec()
        for editor in self.open_editors.values():
            if hasattr(editor, 'editor') and hasattr(editor.editor, 'schedule_rehighlight'):
                editor.editor.schedule_rehighlight()

    def publish_story(self, checked: bool = False) -> None:
        """Open the publish dialog for the current story."""
        if not self.current_story_id:
            QMessageBox.warning(self, "No Story", "Please select a story first.")
            return

        with self.db_manager as conn:
            story = Story.get_by_id(conn, self.current_story_id)

        if not story:
            return

        dialog = PublishDialog(story, self)
        if dialog.exec():
            self._load_unified_canvas()

    def unpublish_story(self, checked: bool = False) -> None:
        """Unpublish and unlock the current story."""
        if not self.current_story_id:
            return

        with self.db_manager as conn:
            story = Story.get_by_id(conn, self.current_story_id)

        if not story or not story.is_locked:
            return

        dialog = UnpublishDialog(story, self)
        if dialog.exec():
            with self.db_manager as conn:
                story.unpublish(conn)

            self._load_unified_canvas()
            self.status_bar.showMessage(f"'{story.title}' unpublished and unlocked")

    def export_project(self, checked: bool = False) -> None:
        """Open the export dialog for the current project."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please open a project first.")
            return

        try:
            with self.db_manager as conn:
                project = Project.get_by_id(conn, self.current_project_id)

            if not project:
                return

            dialog = ExportDialog(project, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")

    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About BlueWriter",
            "BlueWriter v0.1\n\n"
            "A fiction writing tool with timeline-based\n"
            "chapter organization.\n\n"
            "Organize your story using draggable sticky notes\n"
            "on a visual timeline."
        )

    def closeEvent(self, event) -> None:
        """Handle application close - clean up resources."""
        if hasattr(self, 'event_adapter'):
            self.event_adapter.stop()

        for editor in list(self.open_editors.values()):
            editor.close()

        event.accept()
