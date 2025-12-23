"""
Canvas and UI state tools for BlueWriter MCP server.
"""
from typing import Callable
import httpx

from mcp.server.fastmcp import FastMCP


def register_canvas_tools(mcp: FastMCP, get_api_base: Callable[[], str]) -> None:
    """Register canvas and UI state MCP tools.
    
    Args:
        mcp: FastMCP server instance
        get_api_base: Function that returns the API base URL
    """
    
    @mcp.tool()
    def get_canvas_view(story_id: int) -> str:
        """Get the current canvas view state (pan and zoom).
        
        Args:
            story_id: The ID of the story
            
        Returns:
            JSON object with pan_x, pan_y, and zoom values.
        """
        response = httpx.get(f"{get_api_base()}/stories/{story_id}/canvas")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def pan_canvas(story_id: int, x: float, y: float) -> str:
        """Pan the canvas to specific coordinates.
        
        Args:
            story_id: The ID of the story
            x: X coordinate to pan to
            y: Y coordinate to pan to
            
        Returns:
            JSON object with updated view state.
        """
        response = httpx.put(
            f"{get_api_base()}/stories/{story_id}/canvas/pan",
            json={"x": x, "y": y}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def zoom_canvas(story_id: int, zoom: float) -> str:
        """Set the canvas zoom level.
        
        Args:
            story_id: The ID of the story
            zoom: Zoom level (0.1 to 3.0, where 1.0 is 100%)
            
        Returns:
            JSON object with updated view state.
        """
        response = httpx.put(
            f"{get_api_base()}/stories/{story_id}/canvas/zoom",
            json={"zoom": zoom}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def focus_chapter(story_id: int, chapter_id: int) -> str:
        """Pan and zoom the canvas to focus on a specific chapter.
        
        This centers the view on the chapter's sticky note.
        
        Args:
            story_id: The ID of the story
            chapter_id: The ID of the chapter to focus on
            
        Returns:
            JSON object with updated view state.
        """
        response = httpx.post(
            f"{get_api_base()}/stories/{story_id}/canvas/focus",
            json={"chapter_id": chapter_id}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def fit_all_chapters(story_id: int) -> str:
        """Zoom and pan to fit all chapters in view.
        
        Adjusts the view to show all chapter sticky notes.
        
        Args:
            story_id: The ID of the story
            
        Returns:
            JSON object with updated view state.
        """
        response = httpx.post(f"{get_api_base()}/stories/{story_id}/canvas/fit")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def get_canvas_layout(story_id: int) -> str:
        """Get all chapter positions on the canvas.
        
        Returns the layout of all chapter sticky notes.
        
        Args:
            story_id: The ID of the story
            
        Returns:
            JSON object with story_id and array of chapters with
            their positions and colors.
        """
        response = httpx.get(f"{get_api_base()}/stories/{story_id}/canvas/layout")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def reset_canvas(story_id: int) -> str:
        """Reset the canvas view to default position and zoom.
        
        Args:
            story_id: The ID of the story
            
        Returns:
            JSON object with reset view state.
        """
        response = httpx.post(f"{get_api_base()}/stories/{story_id}/canvas/reset")
        response.raise_for_status()
        return response.text
    
    # === Application State Tools ===
    
    @mcp.tool()
    def get_app_state() -> str:
        """Get the current BlueWriter application state.
        
        Returns:
            JSON object with current_project_id, current_story_id,
            and list of open editors.
        """
        response = httpx.get(f"{get_api_base()}/state")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def list_open_editors() -> str:
        """List all currently open editors.
        
        Returns:
            JSON array of open editors with editor_type, item_id,
            and is_modified status.
        """
        response = httpx.get(f"{get_api_base()}/state/editors")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def save_all() -> str:
        """Save all unsaved changes in open editors.
        
        Returns:
            JSON object with items_saved count, success status,
            and message.
        """
        response = httpx.post(f"{get_api_base()}/state/save-all")
        response.raise_for_status()
        return response.text
