"""
Main window for BlueWriter application.
Integrates all UI components: sidebar, timeline canvas, and dialogs.
"""
from PySide6.QtWidgets import (
    QMainWindow, QStatusBar, QToolBar, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from views.timeline_canvas import TimelineCanvas
from views.story_manager import StoryManagerWidget
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
        self.welcome_label = QLabel("Welcome to BlueWriter!\n\nUse File → New Project\nor File → Open Project\nto get started.")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setWordWrap(True)
        self.sidebar_layout.addWidget(self.welcome_label)
        
        self.sidebar_container.setMinimumWidth(200)
        self.sidebar_container.setMaximumWidth(350)
        
        # Story manager (will be created when project loads)
        self.story_manager = None
        
        # Encyclopedia widget (will be created when project loads)
        self.encyclopedia_widget = None
        
        # Right side: Timeline canvas
        self.canvas = TimelineCanvas()
        self.canvas.new_chapter_requested.connect(self.add_chapter_at_position)
        
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
        
        # New Chapter button
        self.new_chapter_action = QAction("New Chapter", self)
        self.new_chapter_action.setShortcut("Ctrl+Shift+N")
        self.new_chapter_action.triggered.connect(self.add_chapter)
        self.new_chapter_action.setEnabled(False)  # Disabled until story selected
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
        """Load a project and set up the story manager and encyclopedia."""
        self.current_project_id = project_id
        self.current_story_id = None
        
        # Get project info for title
        with self.db_manager as conn:
            project = Project.get_by_id(conn, project_id)
            if project:
                self.setWindowTitle(f"BlueWriter - {project.name}")
        
        # Clear old sidebar content
        if self.story_manager:
            self.sidebar_layout.removeWidget(self.story_manager)
            self.story_manager.deleteLater()
        
        if self.encyclopedia_widget:
            self.sidebar_layout.removeWidget(self.encyclopedia_widget)
            self.encyclopedia_widget.deleteLater()
        
        # Hide welcome message
        self.welcome_label.hide()
        
        # Create story manager for this project (top of sidebar)
        self.story_manager = StoryManagerWidget(project_id, self)
        self.story_manager.story_selected.connect(self.on_story_selected)
        self.sidebar_layout.insertWidget(0, self.story_manager)
        
        # Create encyclopedia widget (bottom of sidebar)
        self.encyclopedia_widget = EncyclopediaWidget(project_id, self)
        self.sidebar_layout.addWidget(self.encyclopedia_widget)
        
        # Enable export action
        self.export_action.setEnabled(True)
        
        self.status_bar.showMessage(f"Project loaded. Create or select a story.")
        self.clear_canvas()
    
    def on_story_selected(self, story_id: int) -> None:
        """Handle story selection - load chapters onto canvas."""
        self.current_story_id = story_id
        self.new_chapter_action.setEnabled(True)
        self.load_chapters()
        
        with self.db_manager as conn:
            story = Story.get_by_id(conn, story_id)
            if story:
                self.status_bar.showMessage(f"Editing: {story.title}")
                
                # Update publish action states
                self.publish_story_action.setEnabled(not story.is_locked)
                self.unpublish_story_action.setEnabled(story.is_locked)
                
                # Disable new chapter if locked
                self.new_chapter_action.setEnabled(not story.is_locked)
    
    def load_chapters(self) -> None:
        """Load chapters for current story and display as sticky notes."""
        self.clear_canvas()
        
        if not self.current_story_id:
            return
        
        with self.db_manager as conn:
            chapters = Chapter.get_by_story(conn, self.current_story_id)
            
            for chapter in chapters:
                self.add_sticky_note(chapter)
    
    def clear_canvas(self) -> None:
        """Remove all sticky notes from canvas."""
        for note in self.sticky_notes:
            note.setParent(None)
            note.deleteLater()
        self.sticky_notes.clear()
        self.canvas.update()

    def add_chapter(self) -> None:
        """Create a new chapter and add it to the canvas."""
        if not self.current_story_id:
            QMessageBox.warning(self, "No Story Selected", 
                              "Please select or create a story first.")
            return
        
        # Create new chapter in database
        with self.db_manager as conn:
            # Get count for default position
            existing = Chapter.get_by_story(conn, self.current_story_id)
            x_pos = 100 + (len(existing) * 180)  # Offset each new chapter
            y_pos = 200
            
            chapter = Chapter.create(
                conn,
                story_id=self.current_story_id,
                title=f"Chapter {len(existing) + 1}",
                summary="Click to add summary...",
                content=""
            )
            # Set initial position
            chapter.board_x = x_pos
            chapter.board_y = y_pos
            chapter.update(conn)
            
            # Add sticky note to canvas
            self.add_sticky_note(chapter)
            
            # Open editor immediately
            self.open_chapter_editor(chapter)
        
        self.status_bar.showMessage("New chapter created")
    
    def add_chapter_at_position(self, x: float, y: float) -> None:
        """Create a new chapter at specific canvas position (from right-click)."""
        if not self.current_story_id:
            QMessageBox.warning(self, "No Story Selected", 
                              "Please select or create a story first.")
            return
        
        with self.db_manager as conn:
            existing = Chapter.get_by_story(conn, self.current_story_id)
            
            chapter = Chapter.create(
                conn,
                story_id=self.current_story_id,
                title=f"Chapter {len(existing) + 1}",
                summary="Click to add summary...",
                content=""
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
        # Check if story is locked
        with self.db_manager as conn:
            chapter = Chapter.get_by_id(conn, chapter_id)
            if chapter:
                story = Story.get_by_id(conn, chapter.story_id)
                if story and story.is_locked:
                    QMessageBox.information(
                        self,
                        "Story Locked",
                        f"'{story.title}' is final published and locked.\n\n"
                        "Use File → Publish → Unpublish to unlock for editing."
                    )
                    return
        
        # Check if already open
        if chapter_id in self.open_editors:
            # Bring existing editor to front
            editor = self.open_editors[chapter_id]
            editor.show()
            editor.raise_()
            editor.setFocus()
            return
        
        if chapter:
            self.open_chapter_editor(chapter)
    
    def open_chapter_editor(self, chapter: Chapter) -> None:
        """Open a dockable chapter editor."""
        # Check if already open
        if chapter.id in self.open_editors:
            editor = self.open_editors[chapter.id]
            editor.show()
            editor.raise_()
            return
        
        # Create new dockable editor
        editor = ChapterEditorDock(chapter, self)
        editor.chapter_saved.connect(self.on_chapter_saved)
        editor.chapter_closed.connect(self.on_editor_closed)
        
        # Add to main window as dock widget
        self.addDockWidget(Qt.RightDockWidgetArea, editor)
        
        # Make it float initially for a cleaner experience
        editor.setFloating(True)
        editor.resize(700, 500)
        
        # Track the open editor
        self.open_editors[chapter.id] = editor
    
    def on_editor_closed(self, chapter_id: int) -> None:
        """Handle editor close - remove from tracking."""
        if chapter_id in self.open_editors:
            del self.open_editors[chapter_id]
    
    def on_chapter_saved(self, chapter: Chapter) -> None:
        """Handle chapter save - update sticky note display."""
        # Find and update the corresponding sticky note
        for note in self.sticky_notes:
            if note.chapter.id == chapter.id:
                note.update_from_chapter(chapter)
                # Reposition in case coordinates changed
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
    
    def save_project(self) -> None:
        """Save current project state."""
        # Currently auto-saves on each action, but this could batch
        self.status_bar.showMessage("Project saved")
    
    def refresh_canvas(self) -> None:
        """Reload chapters from database."""
        self.load_chapters()
        self.status_bar.showMessage("Canvas refreshed")
    
    def open_dictionary_editor(self) -> None:
        """Open the custom dictionary editor dialog."""
        dialog = DictionaryEditorDialog(self)
        dialog.exec()
        # Rehighlight all open editors after dictionary changes
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
            # Refresh story state
            self.on_story_selected(self.current_story_id)
            if self.story_manager:
                self.story_manager.load_stories()
    
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
            
            # Refresh story state
            self.on_story_selected(self.current_story_id)
            if self.story_manager:
                self.story_manager.load_stories()
            
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
