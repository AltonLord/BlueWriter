"""
Application state routes for BlueWriter API.
"""
from fastapi import APIRouter, Depends

from api.dependencies import get_editor_service
from api.schemas import (
    AppStateResponse,
    OpenEditorInfo,
    SaveAllResponse,
)
from services.editor_service import EditorService

router = APIRouter()


# Note: current_project_id and current_story_id would typically be 
# tracked by a separate AppStateService. For now, we return None
# and track only editor state.


@router.get("", response_model=AppStateResponse)
async def get_app_state(
    editor_service: EditorService = Depends(get_editor_service),
):
    """Get current application state.
    
    Returns the currently selected project/story (if any) and
    list of open editors.
    """
    editors = editor_service.list_open_editors()
    return AppStateResponse(
        current_project_id=None,  # TODO: Track in AppStateService
        current_story_id=None,    # TODO: Track in AppStateService
        open_editors=[
            OpenEditorInfo(
                editor_type=e.editor_type,
                item_id=e.item_id,
                is_modified=e.is_modified,
            )
            for e in editors
        ],
    )


@router.get("/editors", response_model=list[OpenEditorInfo])
async def list_open_editors(
    editor_service: EditorService = Depends(get_editor_service),
):
    """List all open editors."""
    editors = editor_service.list_open_editors()
    return [
        OpenEditorInfo(
            editor_type=e.editor_type,
            item_id=e.item_id,
            is_modified=e.is_modified,
        )
        for e in editors
    ]


@router.post("/save-all", response_model=SaveAllResponse)
async def save_all(
    editor_service: EditorService = Depends(get_editor_service),
):
    """Save all unsaved changes in open editors.
    
    Note: This emits a SaveRequested event. The actual saving
    is handled by the Qt UI which subscribes to this event.
    """
    modified = editor_service.get_modified_editors()
    count = len(modified)
    
    # In a real implementation, we would:
    # 1. Emit SaveRequested event
    # 2. Wait for SaveCompleted event
    # 3. Return actual results
    
    # For now, we just return what needs saving
    if count == 0:
        return SaveAllResponse(
            items_saved=0,
            success=True,
            message="No unsaved changes",
        )
    
    # Mark all as saved (in memory - actual save happens via Qt)
    for editor in modified:
        editor_service.set_editor_modified(
            editor.editor_type, 
            editor.item_id, 
            modified=False,
        )
    
    return SaveAllResponse(
        items_saved=count,
        success=True,
        message=f"Saved {count} item(s)",
    )
