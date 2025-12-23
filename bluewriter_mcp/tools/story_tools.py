"""
Story management tools for BlueWriter MCP server.
"""
from typing import Callable, List
import httpx

from mcp.server.fastmcp import FastMCP


def register_story_tools(mcp: FastMCP, get_api_base: Callable[[], str]) -> None:
    """Register story-related MCP tools.
    
    Args:
        mcp: FastMCP server instance
        get_api_base: Function that returns the API base URL
    """
    
    @mcp.tool()
    def list_stories(project_id: int) -> str:
        """List all stories in a project.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            JSON array of stories with id, title, synopsis, status,
            sort_order, is_locked, and is_published fields.
        """
        response = httpx.get(f"{get_api_base()}/projects/{project_id}/stories")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def get_story(story_id: int) -> str:
        """Get details of a specific story.
        
        Args:
            story_id: The ID of the story to retrieve
            
        Returns:
            JSON object with story details including status and lock state.
        """
        response = httpx.get(f"{get_api_base()}/stories/{story_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def create_story(project_id: int, title: str, synopsis: str = "") -> str:
        """Create a new story in a project.
        
        Args:
            project_id: The ID of the project to add the story to
            title: The title of the new story
            synopsis: Optional synopsis/summary of the story
            
        Returns:
            JSON object with the created story details.
        """
        response = httpx.post(
            f"{get_api_base()}/projects/{project_id}/stories",
            json={"title": title, "synopsis": synopsis}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def update_story(
        story_id: int, 
        title: str = None, 
        synopsis: str = None
    ) -> str:
        """Update a story's title or synopsis.
        
        Note: Cannot update stories that are final_published (locked).
        Use unpublish_story first to unlock.
        
        Args:
            story_id: The ID of the story to update
            title: New title for the story (optional)
            synopsis: New synopsis for the story (optional)
            
        Returns:
            JSON object with the updated story details.
        """
        data = {}
        if title is not None:
            data["title"] = title
        if synopsis is not None:
            data["synopsis"] = synopsis
        
        response = httpx.put(
            f"{get_api_base()}/stories/{story_id}",
            json=data
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def delete_story(story_id: int) -> str:
        """Delete a story and all its chapters.
        
        Note: Cannot delete stories that are final_published (locked).
        Use unpublish_story first to unlock.
        
        Args:
            story_id: The ID of the story to delete
            
        Returns:
            Confirmation message.
        """
        response = httpx.delete(f"{get_api_base()}/stories/{story_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def select_story(story_id: int) -> str:
        """Select a story in the BlueWriter UI.
        
        This will display the story's chapters on the canvas.
        
        Args:
            story_id: The ID of the story to select
            
        Returns:
            Confirmation message.
        """
        response = httpx.post(f"{get_api_base()}/stories/{story_id}/select")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def publish_story(story_id: int, final: bool = False) -> str:
        """Publish a story.
        
        Publishing marks a story as complete. There are two levels:
        - Rough publish (final=False): Story is published but still editable
        - Final publish (final=True): Story is locked and cannot be edited
        
        Args:
            story_id: The ID of the story to publish
            final: If True, publish as final (locks the story)
            
        Returns:
            JSON object with the updated story details.
        """
        response = httpx.post(
            f"{get_api_base()}/stories/{story_id}/publish",
            json={"final": final}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def unpublish_story(story_id: int) -> str:
        """Unpublish a story, reverting it to draft status.
        
        This unlocks a final_published story, allowing edits again.
        
        Args:
            story_id: The ID of the story to unpublish
            
        Returns:
            JSON object with the updated story details.
        """
        response = httpx.post(f"{get_api_base()}/stories/{story_id}/unpublish")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def reorder_stories(project_id: int, story_ids: List[int]) -> str:
        """Reorder stories within a project.
        
        Args:
            project_id: The ID of the project
            story_ids: List of story IDs in the desired order
            
        Returns:
            Confirmation message.
        """
        response = httpx.put(
            f"{get_api_base()}/projects/{project_id}/stories/order",
            json={"story_ids": story_ids}
        )
        response.raise_for_status()
        return response.text
