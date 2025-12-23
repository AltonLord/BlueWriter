"""
Chapter management tools for BlueWriter MCP server.
"""
from typing import Callable
import httpx

from mcp.server.fastmcp import FastMCP


def register_chapter_tools(mcp: FastMCP, get_api_base: Callable[[], str]) -> None:
    """Register chapter-related MCP tools.
    
    Args:
        mcp: FastMCP server instance
        get_api_base: Function that returns the API base URL
    """
    
    @mcp.tool()
    def list_chapters(story_id: int) -> str:
        """List all chapters in a story.
        
        Args:
            story_id: The ID of the story
            
        Returns:
            JSON array of chapters with id, title, summary, board_x, 
            board_y, and color fields.
        """
        response = httpx.get(f"{get_api_base()}/stories/{story_id}/chapters")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def get_chapter(chapter_id: int) -> str:
        """Get a chapter's details including its content.
        
        Args:
            chapter_id: The ID of the chapter to retrieve
            
        Returns:
            JSON object with full chapter details including content.
        """
        response = httpx.get(f"{get_api_base()}/chapters/{chapter_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def create_chapter(
        story_id: int,
        title: str,
        board_x: int = 100,
        board_y: int = 100,
        color: str = "#FFFF88"
    ) -> str:
        """Create a new chapter in a story.
        
        The chapter appears as a sticky note on the canvas at the 
        specified position.
        
        Args:
            story_id: The ID of the story to add the chapter to
            title: The title of the new chapter
            board_x: X position on canvas (default: 100)
            board_y: Y position on canvas (default: 100)
            color: Sticky note color as hex, e.g. "#FFFF88" (default: yellow)
            
        Returns:
            JSON object with the created chapter details.
        """
        response = httpx.post(
            f"{get_api_base()}/stories/{story_id}/chapters",
            json={
                "title": title,
                "board_x": board_x,
                "board_y": board_y,
                "color": color,
            }
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def update_chapter(
        chapter_id: int,
        title: str = None,
        summary: str = None,
        content: str = None
    ) -> str:
        """Update a chapter's metadata (title, summary, or content).
        
        Note: Cannot update chapters in final_published (locked) stories.
        
        Args:
            chapter_id: The ID of the chapter to update
            title: New title for the chapter (optional)
            summary: New summary for the chapter (optional)
            content: New content for the chapter (optional, HTML format)
            
        Returns:
            JSON object with the updated chapter details.
        """
        data = {}
        if title is not None:
            data["title"] = title
        if summary is not None:
            data["summary"] = summary
        if content is not None:
            data["content"] = content
        
        response = httpx.put(
            f"{get_api_base()}/chapters/{chapter_id}",
            json=data
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def delete_chapter(chapter_id: int) -> str:
        """Delete a chapter.
        
        Note: Cannot delete chapters in final_published (locked) stories.
        
        Args:
            chapter_id: The ID of the chapter to delete
            
        Returns:
            Confirmation message.
        """
        response = httpx.delete(f"{get_api_base()}/chapters/{chapter_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def move_chapter(chapter_id: int, board_x: int, board_y: int) -> str:
        """Move a chapter's sticky note on the canvas.
        
        Args:
            chapter_id: The ID of the chapter to move
            board_x: New X position on canvas
            board_y: New Y position on canvas
            
        Returns:
            JSON object with the updated chapter details.
        """
        response = httpx.put(
            f"{get_api_base()}/chapters/{chapter_id}/position",
            json={"board_x": board_x, "board_y": board_y}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def set_chapter_color(chapter_id: int, color: str) -> str:
        """Change a chapter's sticky note color.
        
        Args:
            chapter_id: The ID of the chapter
            color: New color as hex, e.g. "#FF8888" for red, 
                   "#88FF88" for green, "#8888FF" for blue
            
        Returns:
            JSON object with the updated chapter details.
        """
        response = httpx.put(
            f"{get_api_base()}/chapters/{chapter_id}/color",
            json={"color": color}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def get_chapter_text(chapter_id: int) -> str:
        """Get a chapter's content as plain text.
        
        Strips HTML formatting to return just the text content.
        Useful for reading or analyzing the content.
        
        Args:
            chapter_id: The ID of the chapter
            
        Returns:
            Plain text content of the chapter.
        """
        response = httpx.get(f"{get_api_base()}/chapters/{chapter_id}/text")
        response.raise_for_status()
        return response.json().get("message", "")
    
    @mcp.tool()
    def set_chapter_content(
        chapter_id: int, 
        content: str, 
        format: str = "text"
    ) -> str:
        """Set a chapter's content.
        
        Args:
            chapter_id: The ID of the chapter
            content: The new content to set
            format: Content format - "text" for plain text or "html" for rich text
            
        Returns:
            JSON object with the updated chapter details.
        """
        response = httpx.put(
            f"{get_api_base()}/chapters/{chapter_id}/content",
            json={"content": content, "format": format}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def insert_scene_break(chapter_id: int, position: int = -1) -> str:
        """Insert a scene break (***) into a chapter.
        
        Scene breaks are used to separate scenes within a chapter.
        
        Args:
            chapter_id: The ID of the chapter
            position: Position to insert (-1 for end of chapter)
            
        Returns:
            JSON object with the updated chapter details.
        """
        response = httpx.post(
            f"{get_api_base()}/chapters/{chapter_id}/scene-break",
            json={"position": position}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def open_chapter(chapter_id: int) -> str:
        """Open a chapter in the BlueWriter editor.
        
        This opens a floating editor window for the chapter.
        
        Args:
            chapter_id: The ID of the chapter to open
            
        Returns:
            Confirmation message.
        """
        response = httpx.post(f"{get_api_base()}/chapters/{chapter_id}/open")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def close_chapter(chapter_id: int) -> str:
        """Close a chapter's editor window.
        
        Args:
            chapter_id: The ID of the chapter to close
            
        Returns:
            Confirmation message.
        """
        response = httpx.post(f"{get_api_base()}/chapters/{chapter_id}/close")
        response.raise_for_status()
        return response.text
