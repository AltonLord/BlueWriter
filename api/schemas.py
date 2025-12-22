"""
Pydantic schemas for BlueWriter API.

Defines request/response models for all API endpoints.
Uses Pydantic v2 for validation and serialization.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Project Schemas
# =============================================================================

class ProjectBase(BaseModel):
    """Base schema for project data."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# =============================================================================
# Story Schemas
# =============================================================================

class StoryBase(BaseModel):
    """Base schema for story data."""
    title: str = Field(..., min_length=1, max_length=200, description="Story title")
    synopsis: Optional[str] = Field(None, description="Story synopsis")


class StoryCreate(StoryBase):
    """Schema for creating a new story."""
    pass


class StoryUpdate(BaseModel):
    """Schema for updating a story. All fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    synopsis: Optional[str] = None


class StoryResponse(StoryBase):
    """Schema for story response."""
    id: int
    project_id: int
    sort_order: int
    status: str
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_locked: bool = False
    is_published: bool = False
    
    model_config = {"from_attributes": True}


class StoryPublishRequest(BaseModel):
    """Schema for publishing a story."""
    final: bool = Field(False, description="If True, publish as final (locks story)")


class StoryReorderRequest(BaseModel):
    """Schema for reordering stories."""
    story_ids: List[int] = Field(..., description="Story IDs in desired order")


# =============================================================================
# Chapter Schemas
# =============================================================================

class ChapterBase(BaseModel):
    """Base schema for chapter data."""
    title: str = Field(..., min_length=1, max_length=200, description="Chapter title")


class ChapterCreate(ChapterBase):
    """Schema for creating a new chapter."""
    board_x: int = Field(100, ge=0, description="X position on canvas")
    board_y: int = Field(100, ge=0, description="Y position on canvas")
    color: str = Field("#FFFF88", pattern=r"^#[0-9A-Fa-f]{6}$", description="Sticky note color")


class ChapterUpdate(BaseModel):
    """Schema for updating a chapter. All fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    summary: Optional[str] = None
    content: Optional[str] = None


class ChapterResponse(ChapterBase):
    """Schema for chapter response."""
    id: int
    story_id: int
    summary: Optional[str] = None
    content: Optional[str] = None
    board_x: int
    board_y: int
    color: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class ChapterContentUpdate(BaseModel):
    """Schema for updating chapter content."""
    content: str = Field(..., description="New content")
    format: str = Field("html", pattern=r"^(html|text)$", description="Content format")


class ChapterPositionUpdate(BaseModel):
    """Schema for moving a chapter on canvas."""
    board_x: int = Field(..., ge=0, description="New X position")
    board_y: int = Field(..., ge=0, description="New Y position")


class ChapterColorUpdate(BaseModel):
    """Schema for changing chapter color."""
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="New color")


class SceneBreakRequest(BaseModel):
    """Schema for inserting a scene break."""
    position: int = Field(-1, description="Position to insert (-1 for end)")


# =============================================================================
# Encyclopedia Schemas
# =============================================================================

class EncyclopediaEntryBase(BaseModel):
    """Base schema for encyclopedia entry."""
    name: str = Field(..., min_length=1, max_length=200, description="Entry name")
    category: str = Field(..., min_length=1, description="Entry category")


class EncyclopediaEntryCreate(EncyclopediaEntryBase):
    """Schema for creating an encyclopedia entry."""
    content: Optional[str] = Field("", description="Entry content")
    tags: Optional[str] = Field("", description="Comma-separated tags")


class EncyclopediaEntryUpdate(BaseModel):
    """Schema for updating an encyclopedia entry. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None


class EncyclopediaEntryResponse(EncyclopediaEntryBase):
    """Schema for encyclopedia entry response."""
    id: int
    project_id: int
    content: Optional[str] = None
    tags: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# =============================================================================
# Canvas Schemas
# =============================================================================

class CanvasViewResponse(BaseModel):
    """Schema for canvas view state."""
    pan_x: float
    pan_y: float
    zoom: float


class CanvasPanRequest(BaseModel):
    """Schema for panning the canvas."""
    x: float = Field(..., description="X position")
    y: float = Field(..., description="Y position")


class CanvasZoomRequest(BaseModel):
    """Schema for zooming the canvas."""
    zoom: float = Field(..., ge=0.1, le=3.0, description="Zoom level (0.1-3.0)")


class CanvasFocusRequest(BaseModel):
    """Schema for focusing on a chapter."""
    chapter_id: int = Field(..., description="Chapter ID to focus on")


class ChapterLayoutItem(BaseModel):
    """Schema for a chapter's position in layout."""
    chapter_id: int
    title: str
    board_x: int
    board_y: int
    color: str


class CanvasLayoutResponse(BaseModel):
    """Schema for canvas layout (all chapter positions)."""
    story_id: int
    chapters: List[ChapterLayoutItem]


# =============================================================================
# State Schemas
# =============================================================================

class OpenEditorInfo(BaseModel):
    """Schema for an open editor."""
    editor_type: str
    item_id: int
    is_modified: bool


class AppStateResponse(BaseModel):
    """Schema for application state."""
    current_project_id: Optional[int] = None
    current_story_id: Optional[int] = None
    open_editors: List[OpenEditorInfo] = []


class SaveAllResponse(BaseModel):
    """Schema for save-all response."""
    items_saved: int
    success: bool
    message: str


# =============================================================================
# Common Schemas
# =============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str


__all__ = [
    # Project
    'ProjectCreate', 'ProjectUpdate', 'ProjectResponse',
    # Story
    'StoryCreate', 'StoryUpdate', 'StoryResponse', 
    'StoryPublishRequest', 'StoryReorderRequest',
    # Chapter
    'ChapterCreate', 'ChapterUpdate', 'ChapterResponse',
    'ChapterContentUpdate', 'ChapterPositionUpdate', 
    'ChapterColorUpdate', 'SceneBreakRequest',
    # Encyclopedia
    'EncyclopediaEntryCreate', 'EncyclopediaEntryUpdate', 
    'EncyclopediaEntryResponse',
    # Canvas
    'CanvasViewResponse', 'CanvasPanRequest', 'CanvasZoomRequest',
    'CanvasFocusRequest', 'ChapterLayoutItem', 'CanvasLayoutResponse',
    # State
    'OpenEditorInfo', 'AppStateResponse', 'SaveAllResponse',
    # Common
    'ErrorResponse', 'MessageResponse',
]
