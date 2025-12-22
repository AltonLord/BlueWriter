"""
Project routes for BlueWriter API.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_project_service
from api.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    MessageResponse,
)
from services.project_service import ProjectService

router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    service: ProjectService = Depends(get_project_service),
):
    """List all projects."""
    projects = service.list_projects()
    return [ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        created_at=p.created_at,
        updated_at=p.updated_at,
    ) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
):
    """Create a new project."""
    try:
        project = service.create_project(
            name=data.name,
            description=data.description or "",
        )
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
):
    """Get a project by ID."""
    try:
        project = service.get_project(project_id)
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
):
    """Update a project."""
    try:
        project = service.update_project(
            project_id=project_id,
            name=data.name,
            description=data.description,
        )
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
):
    """Delete a project."""
    try:
        service.delete_project(project_id)
        return MessageResponse(message=f"Project {project_id} deleted")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/open", response_model=MessageResponse)
async def open_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
):
    """Open/select a project in the UI."""
    try:
        service.open_project(project_id)
        return MessageResponse(message=f"Project {project_id} opened")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
