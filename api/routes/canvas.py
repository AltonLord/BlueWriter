"""
Canvas routes for BlueWriter API.
"""
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_canvas_service, get_chapter_service
from api.schemas import (
    CanvasViewResponse,
    CanvasPanRequest,
    CanvasZoomRequest,
    CanvasFocusRequest,
    CanvasLayoutResponse,
    ChapterLayoutItem,
    MessageResponse,
)
from services.canvas_service import CanvasService
from services.chapter_service import ChapterService

router = APIRouter()


@router.get("/stories/{story_id}/canvas", response_model=CanvasViewResponse)
async def get_canvas_view(
    story_id: int,
    service: CanvasService = Depends(get_canvas_service),
):
    """Get current canvas view state (pan/zoom)."""
    view = service.get_view(story_id)
    return CanvasViewResponse(
        pan_x=view.pan_x,
        pan_y=view.pan_y,
        zoom=view.zoom,
    )


@router.put("/stories/{story_id}/canvas/pan", response_model=CanvasViewResponse)
async def pan_canvas(
    story_id: int,
    data: CanvasPanRequest,
    service: CanvasService = Depends(get_canvas_service),
):
    """Pan the canvas to specific coordinates."""
    view = service.set_pan(story_id, data.x, data.y)
    return CanvasViewResponse(
        pan_x=view.pan_x,
        pan_y=view.pan_y,
        zoom=view.zoom,
    )


@router.put("/stories/{story_id}/canvas/zoom", response_model=CanvasViewResponse)
async def zoom_canvas(
    story_id: int,
    data: CanvasZoomRequest,
    service: CanvasService = Depends(get_canvas_service),
):
    """Set canvas zoom level."""
    view = service.set_zoom(story_id, data.zoom)
    return CanvasViewResponse(
        pan_x=view.pan_x,
        pan_y=view.pan_y,
        zoom=view.zoom,
    )


@router.post("/stories/{story_id}/canvas/focus", response_model=CanvasViewResponse)
async def focus_chapter(
    story_id: int,
    data: CanvasFocusRequest,
    chapter_service: ChapterService = Depends(get_chapter_service),
    canvas_service: CanvasService = Depends(get_canvas_service),
):
    """Pan and zoom to center on a specific chapter."""
    try:
        chapter = chapter_service.get_chapter(data.chapter_id)
        view = canvas_service.focus_chapter(story_id, chapter.board_x, chapter.board_y)
        return CanvasViewResponse(
            pan_x=view.pan_x,
            pan_y=view.pan_y,
            zoom=view.zoom,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/stories/{story_id}/canvas/fit", response_model=CanvasViewResponse)
async def fit_all_chapters(
    story_id: int,
    chapter_service: ChapterService = Depends(get_chapter_service),
    canvas_service: CanvasService = Depends(get_canvas_service),
):
    """Fit all chapters in view."""
    chapters = chapter_service.list_chapters(story_id)
    positions = [(c.board_x, c.board_y) for c in chapters]
    view = canvas_service.fit_all(story_id, positions if positions else None)
    return CanvasViewResponse(
        pan_x=view.pan_x,
        pan_y=view.pan_y,
        zoom=view.zoom,
    )


@router.get("/stories/{story_id}/canvas/layout", response_model=CanvasLayoutResponse)
async def get_canvas_layout(
    story_id: int,
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    """Get all chapter positions for a story."""
    chapters = chapter_service.list_chapters(story_id)
    return CanvasLayoutResponse(
        story_id=story_id,
        chapters=[
            ChapterLayoutItem(
                chapter_id=c.id,
                title=c.title,
                board_x=c.board_x,
                board_y=c.board_y,
                color=c.color,
            )
            for c in chapters
        ],
    )


@router.post("/stories/{story_id}/canvas/reset", response_model=CanvasViewResponse)
async def reset_canvas(
    story_id: int,
    service: CanvasService = Depends(get_canvas_service),
):
    """Reset canvas view to defaults."""
    view = service.reset_view(story_id)
    return CanvasViewResponse(
        pan_x=view.pan_x,
        pan_y=view.pan_y,
        zoom=view.zoom,
    )
