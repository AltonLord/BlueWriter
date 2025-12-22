"""
Export module for BlueWriter.
Handles exporting projects to portable formats (Markdown + JSON).
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import zipfile
import tempfile
import shutil

from models.project import Project
from models.story import Story
from models.chapter import Chapter
from models.encyclopedia_entry import EncyclopediaEntry
from database.connection import DatabaseManager
from utils.publishing import html_to_text


class ProjectExporter:
    """Handles exporting projects to various formats."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def export_project(self, project_id: int, output_path: str) -> str:
        """
        Export a complete project to a zip archive.
        
        Structure:
        project_name/
        ├── project.json          # Project metadata
        ├── stories/
        │   ├── story_1/
        │   │   ├── story.json    # Story metadata
        │   │   ├── chapter_01_title.md
        │   │   ├── chapter_02_title.md
        │   │   └── ...
        │   └── story_2/
        │       └── ...
        └── encyclopedia/
            ├── entries.json      # All entries metadata
            ├── Character/
            │   ├── entry_name.md
            │   └── ...
            └── Location/
                └── ...
        
        Args:
            project_id: ID of the project to export
            output_path: Path for the output zip file
            
        Returns:
            Path to the created zip file
        """
        with DatabaseManager(self.db_path) as conn:
            project = Project.get_by_id(conn, project_id)
            if not project:
                raise ValueError(f"Project with ID {project_id} not found")
            
            stories = Story.get_by_project(conn, project_id)
            encyclopedia_entries = EncyclopediaEntry.get_by_project(conn, project_id)
        
        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / self._safe_filename(project.name)
            base_dir.mkdir(parents=True)
            
            # Export project metadata
            self._export_project_metadata(project, stories, base_dir)
            
            # Export stories
            stories_dir = base_dir / "stories"
            stories_dir.mkdir()
            
            for story in stories:
                with DatabaseManager(self.db_path) as conn:
                    chapters = Chapter.get_by_story(conn, story.id)
                self._export_story(story, chapters, stories_dir)
            
            # Export encyclopedia
            if encyclopedia_entries:
                self._export_encyclopedia(encyclopedia_entries, base_dir)
            
            # Create zip archive
            zip_path = shutil.make_archive(
                output_path.replace('.zip', ''),
                'zip',
                temp_dir
            )
            
            return zip_path

    def _safe_filename(self, name: str) -> str:
        """Convert name to safe filename."""
        safe = re.sub(r'[^\w\s-]', '', name).strip()
        return re.sub(r'[-\s]+', '_', safe)
    
    def _export_project_metadata(self, project: Project, stories: list, base_dir: Path) -> None:
        """Export project metadata to JSON."""
        metadata = {
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'exported_at': datetime.now().isoformat(),
            'story_count': len(stories),
            'stories': [
                {
                    'title': s.title,
                    'synopsis': s.synopsis,
                    'status': s.status,
                    'sort_order': s.sort_order
                }
                for s in stories
            ]
        }
        
        with open(base_dir / 'project.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _export_story(self, story: Story, chapters: list, stories_dir: Path) -> None:
        """Export a story and its chapters."""
        story_dir = stories_dir / self._safe_filename(story.title)
        story_dir.mkdir()
        
        # Sort chapters by position
        chapters.sort(key=lambda c: (c.board_y, c.board_x))
        
        # Story metadata
        story_meta = {
            'title': story.title,
            'synopsis': story.synopsis,
            'status': story.status,
            'published_at': story.published_at.isoformat() if story.published_at else None,
            'chapter_count': len(chapters),
            'chapters': []
        }
        
        # Export each chapter
        for i, chapter in enumerate(chapters):
            chapter_num = str(i + 1).zfill(2)
            safe_title = self._safe_filename(chapter.title)
            filename = f"chapter_{chapter_num}_{safe_title}.md"
            
            # Build markdown content
            md_content = f"# {chapter.title}\n\n"
            if chapter.summary:
                md_content += f"*{chapter.summary}*\n\n---\n\n"
            
            # Convert HTML content to text
            text_content = html_to_text(chapter.content)
            md_content += text_content
            
            # Write chapter file
            with open(story_dir / filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # Add to metadata
            story_meta['chapters'].append({
                'title': chapter.title,
                'summary': chapter.summary,
                'filename': filename,
                'board_x': chapter.board_x,
                'board_y': chapter.board_y,
                'color': chapter.color
            })
        
        # Write story metadata
        with open(story_dir / 'story.json', 'w', encoding='utf-8') as f:
            json.dump(story_meta, f, indent=2, ensure_ascii=False)
    
    def _export_encyclopedia(self, entries: list, base_dir: Path) -> None:
        """Export encyclopedia entries."""
        enc_dir = base_dir / "encyclopedia"
        enc_dir.mkdir()
        
        # Group entries by category
        by_category: Dict[str, list] = {}
        for entry in entries:
            cat = entry.category or "General"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(entry)
        
        # Export metadata
        enc_meta = {
            'entry_count': len(entries),
            'categories': list(by_category.keys()),
            'entries': [
                {
                    'name': e.name,
                    'category': e.category,
                    'tags': e.tags,
                    'filename': f"{e.category}/{self._safe_filename(e.name)}.md"
                }
                for e in entries
            ]
        }
        
        with open(enc_dir / 'entries.json', 'w', encoding='utf-8') as f:
            json.dump(enc_meta, f, indent=2, ensure_ascii=False)
        
        # Export entries by category
        for category, cat_entries in by_category.items():
            cat_dir = enc_dir / self._safe_filename(category)
            cat_dir.mkdir()
            
            for entry in cat_entries:
                filename = f"{self._safe_filename(entry.name)}.md"
                
                md_content = f"# {entry.name}\n\n"
                md_content += f"**Category:** {entry.category}\n\n"
                if entry.tags:
                    md_content += f"**Tags:** {entry.tags}\n\n"
                md_content += "---\n\n"
                md_content += html_to_text(entry.content)
                
                with open(cat_dir / filename, 'w', encoding='utf-8') as f:
                    f.write(md_content)


def export_project_to_zip(db_path: str, project_id: int, output_path: str) -> str:
    """Convenience function to export a project."""
    exporter = ProjectExporter(db_path)
    return exporter.export_project(project_id, output_path)
