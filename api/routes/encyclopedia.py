"""
Encyclopedia routes for BlueWriter API.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_encyclopedia_service
from api.schemas import (
    EncyclopediaEntryCreate,
    EncyclopediaEntryUpdate,
    EncyclopediaEntryResponse,
    MessageResponse,
)
from services.encyclopedia_service import EncyclopediaService

router = APIRouter()


def _entry_to_response(entry) -> EncyclopediaEntryResponse:
    """Convert EncyclopediaEntryDTO to EncyclopediaEntryResponse."""
    return EncyclopediaEntryResponse(
        id=entry.id,
        project_id=entry.project_id,
        name=entry.name,
        category=entry.category,
        content=entry.content,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("/projects/{project_id}/encyclopedia", response_model=List[EncyclopediaEntryResponse])
async def list_entries(
    project_id: int,
    category: Optional[str] = Query(None, description="Filter by category"),
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """List encyclopedia entries in a project."""
    entries = service.list_entries(project_id, category=category)
    return [_entry_to_response(e) for e in entries]


@router.get("/projects/{project_id}/encyclopedia/search", response_model=List[EncyclopediaEntryResponse])
async def search_entries(
    project_id: int,
    q: str = Query(..., description="Search query"),
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """Search encyclopedia entries by keyword."""
    entries = service.search_entries(project_id, q)
    return [_entry_to_response(e) for e in entries]


@router.get("/projects/{project_id}/encyclopedia/categories", response_model=List[str])
async def list_categories(
    project_id: int,
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """List all encyclopedia categories for a project."""
    return service.list_categories(project_id)


@router.post("/projects/{project_id}/encyclopedia", response_model=EncyclopediaEntryResponse, status_code=201)
async def create_entry(
    project_id: int,
    data: EncyclopediaEntryCreate,
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """Create a new encyclopedia entry."""
    try:
        entry = service.create_entry(
            project_id=project_id,
            name=data.name,
            category=data.category,
            content=data.content or "",
            tags=data.tags or "",
        )
        return _entry_to_response(entry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/encyclopedia/{entry_id}", response_model=EncyclopediaEntryResponse)
async def get_entry(
    entry_id: int,
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """Get an encyclopedia entry by ID."""
    try:
        entry = service.get_entry(entry_id)
        return _entry_to_response(entry)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/encyclopedia/{entry_id}", response_model=EncyclopediaEntryResponse)
async def update_entry(
    entry_id: int,
    data: EncyclopediaEntryUpdate,
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """Update an encyclopedia entry."""
    try:
        entry = service.update_entry(
            entry_id=entry_id,
            name=data.name,
            category=data.category,
            content=data.content,
            tags=data.tags,
        )
        return _entry_to_response(entry)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/encyclopedia/{entry_id}", response_model=MessageResponse)
async def delete_entry(
    entry_id: int,
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """Delete an encyclopedia entry."""
    try:
        service.delete_entry(entry_id)
        return MessageResponse(message=f"Entry {entry_id} deleted")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/encyclopedia/{entry_id}/open", response_model=MessageResponse)
async def open_entry(
    entry_id: int,
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """Open an encyclopedia entry in the editor."""
    try:
        service.open_entry(entry_id)
        return MessageResponse(message=f"Entry {entry_id} opened")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/encyclopedia/{entry_id}/close", response_model=MessageResponse)
async def close_entry(
    entry_id: int,
    service: EncyclopediaService = Depends(get_encyclopedia_service),
):
    """Close an encyclopedia entry editor."""
    try:
        service.close_entry(entry_id)
        return MessageResponse(message=f"Entry {entry_id} closed")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
