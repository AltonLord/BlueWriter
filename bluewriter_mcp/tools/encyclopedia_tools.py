"""
Encyclopedia tools for BlueWriter MCP server.
"""
from typing import Callable
import httpx

from mcp.server.fastmcp import FastMCP


def register_encyclopedia_tools(mcp: FastMCP, get_api_base: Callable[[], str]) -> None:
    """Register encyclopedia-related MCP tools.
    
    Args:
        mcp: FastMCP server instance
        get_api_base: Function that returns the API base URL
    """
    
    @mcp.tool()
    def list_encyclopedia_entries(project_id: int, category: str = None) -> str:
        """List encyclopedia entries in a project.
        
        The encyclopedia stores world-building information like characters,
        locations, items, events, and other reference material.
        
        Args:
            project_id: The ID of the project
            category: Optional category filter (e.g., "Character", "Location")
            
        Returns:
            JSON array of entries with id, name, category, tags fields.
        """
        url = f"{get_api_base()}/projects/{project_id}/encyclopedia"
        if category:
            url += f"?category={category}"
        response = httpx.get(url)
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def search_encyclopedia(project_id: int, query: str) -> str:
        """Search encyclopedia entries by keyword.
        
        Searches across entry names, content, and tags.
        
        Args:
            project_id: The ID of the project
            query: Search keyword
            
        Returns:
            JSON array of matching entries.
        """
        response = httpx.get(
            f"{get_api_base()}/projects/{project_id}/encyclopedia/search",
            params={"q": query}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def list_encyclopedia_categories(project_id: int) -> str:
        """List all encyclopedia categories in use for a project.
        
        Returns both default categories and any custom categories
        that have been used.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            JSON array of category names.
        """
        response = httpx.get(
            f"{get_api_base()}/projects/{project_id}/encyclopedia/categories"
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def get_encyclopedia_entry(entry_id: int) -> str:
        """Get details of a specific encyclopedia entry.
        
        Args:
            entry_id: The ID of the entry to retrieve
            
        Returns:
            JSON object with full entry details including content.
        """
        response = httpx.get(f"{get_api_base()}/encyclopedia/{entry_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def create_encyclopedia_entry(
        project_id: int,
        name: str,
        category: str,
        content: str = "",
        tags: str = ""
    ) -> str:
        """Create a new encyclopedia entry.
        
        Common categories: Character, Location, Item, Faction, Event, Concept
        
        Args:
            project_id: The ID of the project
            name: Name of the entry (e.g., character name, location name)
            category: Category for the entry (e.g., "Character", "Location")
            content: Description/content for the entry
            tags: Comma-separated tags for organization and search
            
        Returns:
            JSON object with the created entry details.
        """
        response = httpx.post(
            f"{get_api_base()}/projects/{project_id}/encyclopedia",
            json={
                "name": name,
                "category": category,
                "content": content,
                "tags": tags,
            }
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def update_encyclopedia_entry(
        entry_id: int,
        name: str = None,
        category: str = None,
        content: str = None,
        tags: str = None
    ) -> str:
        """Update an encyclopedia entry.
        
        Only provide the fields you want to change.
        
        Args:
            entry_id: The ID of the entry to update
            name: New name for the entry (optional)
            category: New category for the entry (optional)
            content: New content for the entry (optional)
            tags: New comma-separated tags (optional)
            
        Returns:
            JSON object with the updated entry details.
        """
        data = {}
        if name is not None:
            data["name"] = name
        if category is not None:
            data["category"] = category
        if content is not None:
            data["content"] = content
        if tags is not None:
            data["tags"] = tags
        
        response = httpx.put(
            f"{get_api_base()}/encyclopedia/{entry_id}",
            json=data
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def delete_encyclopedia_entry(entry_id: int) -> str:
        """Delete an encyclopedia entry.
        
        Args:
            entry_id: The ID of the entry to delete
            
        Returns:
            Confirmation message.
        """
        response = httpx.delete(f"{get_api_base()}/encyclopedia/{entry_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def open_encyclopedia_entry(entry_id: int) -> str:
        """Open an encyclopedia entry in the BlueWriter editor.
        
        Args:
            entry_id: The ID of the entry to open
            
        Returns:
            Confirmation message.
        """
        response = httpx.post(f"{get_api_base()}/encyclopedia/{entry_id}/open")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def close_encyclopedia_entry(entry_id: int) -> str:
        """Close an encyclopedia entry's editor.
        
        Args:
            entry_id: The ID of the entry to close
            
        Returns:
            Confirmation message.
        """
        response = httpx.post(f"{get_api_base()}/encyclopedia/{entry_id}/close")
        response.raise_for_status()
        return response.text
