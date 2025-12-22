"""
Story routes for BlueWriter API.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_story_service
from api.schemas import (
    StoryCreate,
    StoryUpdate,
    StoryResponse,
    StoryPublishRequest,
    StoryReorderRequest,
    MessageResponse,
)
from services.story_service import StoryService

router = APIRouter()


def _story_to_response(story) -> StoryResponse:
    """Convert StoryDTO to StoryResponse."""
    return StoryResponse(
        id=story.id,
        project_id=story.project_id,
        title=story.title,
        synopsis=story.synopsis,
        sort_order=story.sort_order,
        status=story.status,
        published_at=story.published_at,
        created_at=story.created_at,
        updated_at=story.updated_at,
        is_locked=story.is_locked,
        is_published=story.is_published,
    )


@router.get("/projects/{project_id}/stories", response_model=List[StoryResponse])
async def list_stories(
    project_id: int,
    service: StoryService = Depends(get_story_service),
):
    """List all stories in a project."""
    stories = service.list_stories(project_id)
    return [_story_to_response(s) for s in stories]


@router.post("/projects/{project_id}/stories", response_model=StoryResponse, status_code=201)
async def create_story(
    project_id: int,
    data: StoryCreate,
    service: StoryService = Depends(get_story_service),
):
    """Create a new story in a project."""
    try:
        story = service.create_story(
            project_id=project_id,
            title=data.title,
            synopsis=data.synopsis or "",
        )
        return _story_to_response(story)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stories/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: int,
    service: StoryService = Depends(get_story_service),
):
    """Get a story by ID."""
    try:
        story = service.get_story(story_id)
        return _story_to_response(story)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/stories/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    data: StoryUpdate,
    service: StoryService = Depends(get_story_service),
):
    """Update a story."""
    try:
        story = service.update_story(
            story_id=story_id,
            title=data.title,
            synopsis=data.synopsis,
        )
        return _story_to_response(story)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/stories/{story_id}", response_model=MessageResponse)
async def delete_story(
    story_id: int,
    service: StoryService = Depends(get_story_service),
):
    """Delete a story."""
    try:
        service.delete_story(story_id)
        return MessageResponse(message=f"Story {story_id} deleted")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/stories/{story_id}/select", response_model=MessageResponse)
async def select_story(
    story_id: int,
    service: StoryService = Depends(get_story_service),
):
    """Select a story in the UI."""
    try:
        service.select_story(story_id)
        return MessageResponse(message=f"Story {story_id} selected")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/stories/{story_id}/publish", response_model=StoryResponse)
async def publish_story(
    story_id: int,
    data: StoryPublishRequest,
    service: StoryService = Depends(get_story_service),
):
    """Publish a story (rough or final)."""
    try:
        story = service.publish_story(story_id, final=data.final)
        return _story_to_response(story)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/stories/{story_id}/unpublish", response_model=StoryResponse)
async def unpublish_story(
    story_id: int,
    service: StoryService = Depends(get_story_service),
):
    """Unpublish a story (revert to draft)."""
    try:
        story = service.unpublish_story(story_id)
        return _story_to_response(story)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/projects/{project_id}/stories/order", response_model=MessageResponse)
async def reorder_stories(
    project_id: int,
    data: StoryReorderRequest,
    service: StoryService = Depends(get_story_service),
):
    """Reorder stories in a project."""
    try:
        service.reorder_stories(project_id, data.story_ids)
        return MessageResponse(message="Stories reordered")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
