"""
BlueWriter Service Layer.

This package contains UI-agnostic business logic services.
Services handle all database operations and emit events for state changes.
"""
from services.base import BaseService
from services.project_service import ProjectService, ProjectDTO
from services.story_service import StoryService, StoryDTO

__all__ = [
    'BaseService',
    'ProjectService',
    'ProjectDTO',
    'StoryService',
    'StoryDTO',
]
