"""
Chapter routes for BlueWriter API.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_chapter_service
from api.schemas import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    ChapterContentUpdate,
    ChapterPositionUpdate,
    ChapterColorUpdate,
    SceneBreakRequest,
    MessageResponse,
)
from services.chapter_service import ChapterService

router = APIRouter()


def _chapter_to_response(chapter) -> ChapterResponse:
    """Convert ChapterDTO to ChapterResponse."""
    return ChapterResponse(
        id=chapter.id,
        story_id=chapter.story_id,
        title=chapter.title,
        summary=chapter.summary,
        content=chapter.content,
        board_x=chapter.board_x,
        board_y=chapter.board_y,
        color=chapter.color,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
    )


@router.get("/stories/{story_id}/chapters", response_model=List[ChapterResponse])
async def list_chapters(
    story_id: int,
    service: ChapterService = Depends(get_chapter_service),
):
    """List all chapters in a story."""
    chapters = service.list_chapters(story_id)
    return [_chapter_to_response(c) for c in chapters]


@router.post("/stories/{story_id}/chapters", response_model=ChapterResponse, status_code=201)
async def create_chapter(
    story_id: int,
    data: ChapterCreate,
    service: ChapterService = Depends(get_chapter_service),
):
    """Create a new chapter in a story."""
    try:
        chapter = service.create_chapter(
            story_id=story_id,
            title=data.title,
            board_x=data.board_x,
            board_y=data.board_y,
            color=data.color,
        )
        return _chapter_to_response(chapter)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(
    chapter_id: int,
    service: ChapterService = Depends(get_chapter_service),
):
    """Get a chapter by ID (includes content)."""
    try:
        chapter = service.get_chapter(chapter_id)
        return _chapter_to_response(chapter)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: int,
    data: ChapterUpdate,
    service: ChapterService = Depends(get_chapter_service),
):
    """Update a chapter's metadata."""
    try:
        chapter = service.update_chapter(
            chapter_id=chapter_id,
            title=data.title,
            summary=data.summary,
            content=data.content,
        )
        return _chapter_to_response(chapter)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/chapters/{chapter_id}", response_model=MessageResponse)
async def delete_chapter(
    chapter_id: int,
    service: ChapterService = Depends(get_chapter_service),
):
    """Delete a chapter."""
    try:
        service.delete_chapter(chapter_id)
        return MessageResponse(message=f"Chapter {chapter_id} deleted")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/chapters/{chapter_id}/content", response_model=ChapterResponse)
async def update_chapter_content(
    chapter_id: int,
    data: ChapterContentUpdate,
    service: ChapterService = Depends(get_chapter_service),
):
    """Update chapter content."""
    try:
        if data.format == "html":
            chapter = service.set_chapter_html(chapter_id, data.content)
        else:
            chapter = service.set_chapter_text(chapter_id, data.content)
        return _chapter_to_response(chapter)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/chapters/{chapter_id}/position", response_model=ChapterResponse)
async def move_chapter(
    chapter_id: int,
    data: ChapterPositionUpdate,
    service: ChapterService = Depends(get_chapter_service),
):
    """Move a chapter on the canvas."""
    try:
        chapter = service.move_chapter(chapter_id, data.board_x, data.board_y)
        return _chapter_to_response(chapter)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/chapters/{chapter_id}/color", response_model=ChapterResponse)
async def set_chapter_color(
    chapter_id: int,
    data: ChapterColorUpdate,
    service: ChapterService = Depends(get_chapter_service),
):
    """Change a chapter's sticky note color."""
    try:
        chapter = service.set_chapter_color(chapter_id, data.color)
        return _chapter_to_response(chapter)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/chapters/{chapter_id}/scene-break", response_model=ChapterResponse)
async def insert_scene_break(
    chapter_id: int,
    data: SceneBreakRequest,
    service: ChapterService = Depends(get_chapter_service),
):
    """Insert a scene break into a chapter."""
    try:
        chapter = service.insert_scene_break(chapter_id, data.position)
        return _chapter_to_response(chapter)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/chapters/{chapter_id}/text", response_model=MessageResponse)
async def get_chapter_text(
    chapter_id: int,
    service: ChapterService = Depends(get_chapter_service),
):
    """Get chapter content as plain text."""
    try:
        text = service.get_chapter_text(chapter_id)
        return MessageResponse(message=text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/chapters/{chapter_id}/open", response_model=MessageResponse)
async def open_chapter(
    chapter_id: int,
    service: ChapterService = Depends(get_chapter_service),
):
    """Open a chapter in the editor."""
    try:
        service.open_chapter(chapter_id)
        return MessageResponse(message=f"Chapter {chapter_id} opened")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/chapters/{chapter_id}/close", response_model=MessageResponse)
async def close_chapter(
    chapter_id: int,
    service: ChapterService = Depends(get_chapter_service),
):
    """Close a chapter editor."""
    try:
        service.close_chapter(chapter_id)
        return MessageResponse(message=f"Chapter {chapter_id} closed")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
