"""
Import module for BlueWriter.
Handles importing projects from exported ZIP archives.
"""
import json
import re
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from models.project import Project
from models.story import Story
from models.chapter import Chapter
from models.encyclopedia_entry import EncyclopediaEntry
from database.connection import DatabaseManager


class ProjectImporter:
    """Handles importing projects from various formats."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def import_from_zip(self, zip_path: str) -> Tuple[int, Dict[str, Any]]:
        """
        Import a project from a BlueWriter export ZIP archive.
        
        Args:
            zip_path: Path to the ZIP file to import
            
        Returns:
            Tuple of (project_id, stats_dict)
            stats_dict contains counts of imported items
        """
        stats = {
            'stories': 0,
            'chapters': 0,
            'encyclopedia_entries': 0
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)
            
            # Find project directory (should be single top-level folder)
            temp_path = Path(temp_dir)
            project_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
            
            if not project_dirs:
                raise ValueError("Invalid export: no project directory found")
            
            project_dir = project_dirs[0]
            
            # Load project metadata
            project_json = project_dir / "project.json"
            if not project_json.exists():
                raise ValueError("Invalid export: project.json not found")
            
            with open(project_json, 'r', encoding='utf-8') as f:
                project_meta = json.load(f)
            
            # Create project in database
            with DatabaseManager(self.db_path) as conn:
                # Check for duplicate name and modify if needed
                project_name = self._get_unique_name(conn, project_meta['name'])
                
                project = Project.create(
                    conn,
                    name=project_name,
                    description=project_meta.get('description', '')
                )
                project_id = project.id
            
            # Import stories
            stories_dir = project_dir / "stories"
            if stories_dir.exists():
                for story_dir in sorted(stories_dir.iterdir()):
                    if story_dir.is_dir():
                        chapter_count = self._import_story(project_id, story_dir)
                        stats['stories'] += 1
                        stats['chapters'] += chapter_count
            
            # Import encyclopedia
            enc_dir = project_dir / "encyclopedia"
            if enc_dir.exists():
                enc_count = self._import_encyclopedia(project_id, enc_dir)
                stats['encyclopedia_entries'] = enc_count
        
        return project_id, stats

    def _get_unique_name(self, conn, name: str) -> str:
        """Get a unique project name, adding suffix if needed."""
        # Check if name exists
        projects = Project.get_all(conn)
        existing_names = {p.name for p in projects}
        
        if name not in existing_names:
            return name
        
        # Add suffix
        counter = 1
        while f"{name} ({counter})" in existing_names:
            counter += 1
        
        return f"{name} ({counter})"
    
    def _import_story(self, project_id: int, story_dir: Path) -> int:
        """Import a story and its chapters. Returns chapter count."""
        # Load story metadata
        story_json = story_dir / "story.json"
        if not story_json.exists():
            return 0
        
        with open(story_json, 'r', encoding='utf-8') as f:
            story_meta = json.load(f)
        
        # Create story
        with DatabaseManager(self.db_path) as conn:
            story = Story.create(
                conn,
                project_id=project_id,
                title=story_meta.get('title', 'Untitled'),
                synopsis=story_meta.get('synopsis', '')
            )
            story_id = story.id
        
        # Import chapters
        chapter_count = 0
        chapters_meta = story_meta.get('chapters', [])
        
        for chapter_meta in chapters_meta:
            filename = chapter_meta.get('filename')
            if not filename:
                continue
            
            chapter_file = story_dir / filename
            if not chapter_file.exists():
                continue
            
            # Read markdown content
            with open(chapter_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Parse markdown to extract content (skip title and summary lines)
            content = self._parse_chapter_markdown(md_content)
            
            # Create chapter
            with DatabaseManager(self.db_path) as conn:
                chapter = Chapter.create(
                    conn,
                    story_id=story_id,
                    title=chapter_meta.get('title', 'Untitled'),
                    summary=chapter_meta.get('summary', ''),
                    content=content
                )
                
                # Update position and color
                chapter.board_x = chapter_meta.get('board_x', 100.0)
                chapter.board_y = chapter_meta.get('board_y', 100.0)
                chapter.color = chapter_meta.get('color', '#FFFF88')
                chapter.update(conn)
            
            chapter_count += 1
        
        return chapter_count
    
    def _parse_chapter_markdown(self, md_content: str) -> str:
        """Parse chapter markdown to extract body content."""
        lines = md_content.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            # Skip title line (# Title)
            if line.startswith('# ') and not in_content:
                continue
            # Skip summary line (*summary*)
            if line.startswith('*') and line.endswith('*') and not in_content:
                continue
            # Skip horizontal rule
            if line.strip() == '---':
                in_content = True
                continue
            
            if in_content or (not line.startswith('#') and not line.startswith('*')):
                in_content = True
                content_lines.append(line)
        
        # Convert to simple HTML paragraphs
        text = '\n'.join(content_lines).strip()
        paragraphs = text.split('\n\n')
        html_content = ''
        for para in paragraphs:
            para = para.strip()
            if para:
                html_content += f'<p>{para}</p>\n'
        
        return html_content

    def _import_encyclopedia(self, project_id: int, enc_dir: Path) -> int:
        """Import encyclopedia entries. Returns entry count."""
        # Load entries metadata
        entries_json = enc_dir / "entries.json"
        if not entries_json.exists():
            return 0
        
        with open(entries_json, 'r', encoding='utf-8') as f:
            enc_meta = json.load(f)
        
        entry_count = 0
        
        for entry_meta in enc_meta.get('entries', []):
            filename = entry_meta.get('filename')
            if not filename:
                continue
            
            entry_file = enc_dir / filename
            if not entry_file.exists():
                continue
            
            # Read markdown content
            with open(entry_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Parse markdown to extract content
            content = self._parse_entry_markdown(md_content)
            
            # Create entry
            with DatabaseManager(self.db_path) as conn:
                EncyclopediaEntry.create(
                    conn,
                    project_id=project_id,
                    name=entry_meta.get('name', 'Untitled'),
                    category=entry_meta.get('category', 'General'),
                    content=content,
                    tags=entry_meta.get('tags', '')
                )
            
            entry_count += 1
        
        return entry_count
    
    def _parse_entry_markdown(self, md_content: str) -> str:
        """Parse entry markdown to extract body content."""
        lines = md_content.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            # Skip title line (# Name)
            if line.startswith('# ') and not in_content:
                continue
            # Skip metadata lines (**Category:** etc)
            if line.startswith('**') and ':' in line and not in_content:
                continue
            # Skip horizontal rule
            if line.strip() == '---':
                in_content = True
                continue
            
            if in_content:
                content_lines.append(line)
        
        # Convert to simple HTML paragraphs
        text = '\n'.join(content_lines).strip()
        paragraphs = text.split('\n\n')
        html_content = ''
        for para in paragraphs:
            para = para.strip()
            if para:
                html_content += f'<p>{para}</p>\n'
        
        return html_content


def import_project_from_zip(db_path: str, zip_path: str) -> Tuple[int, Dict[str, Any]]:
    """Convenience function to import a project."""
    importer = ProjectImporter(db_path)
    return importer.import_from_zip(zip_path)
