"""
FastAPI dependency injection for BlueWriter API.

Provides functions to inject services into route handlers.
"""
from fastapi import Request

from services.project_service import ProjectService
from services.story_service import StoryService
from services.chapter_service import ChapterService
from services.encyclopedia_service import EncyclopediaService
from services.canvas_service import CanvasService
from services.editor_service import EditorService


def get_project_service(request: Request) -> ProjectService:
    """Get ProjectService from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ProjectService instance
    """
    return request.app.state.services['project']


def get_story_service(request: Request) -> StoryService:
    """Get StoryService from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        StoryService instance
    """
    return request.app.state.services['story']


def get_chapter_service(request: Request) -> ChapterService:
    """Get ChapterService from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ChapterService instance
    """
    return request.app.state.services['chapter']


def get_encyclopedia_service(request: Request) -> EncyclopediaService:
    """Get EncyclopediaService from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        EncyclopediaService instance
    """
    return request.app.state.services['encyclopedia']


def get_canvas_service(request: Request) -> CanvasService:
    """Get CanvasService from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        CanvasService instance
    """
    return request.app.state.services['canvas']


def get_editor_service(request: Request) -> EditorService:
    """Get EditorService from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        EditorService instance
    """
    return request.app.state.services['editor']


__all__ = [
    'get_project_service',
    'get_story_service',
    'get_chapter_service',
    'get_encyclopedia_service',
    'get_canvas_service',
    'get_editor_service',
]
