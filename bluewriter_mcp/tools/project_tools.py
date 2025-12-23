"""
Project management tools for BlueWriter MCP server.
"""
from typing import Callable
import httpx

from mcp.server.fastmcp import FastMCP


def register_project_tools(mcp: FastMCP, get_api_base: Callable[[], str]) -> None:
    """Register project-related MCP tools.
    
    Args:
        mcp: FastMCP server instance
        get_api_base: Function that returns the API base URL
    """
    
    @mcp.tool()
    def list_projects() -> str:
        """List all BlueWriter projects.
        
        Returns a JSON array of projects with id, name, description, 
        created_at, and updated_at fields.
        """
        response = httpx.get(f"{get_api_base()}/projects")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def get_project(project_id: int) -> str:
        """Get details of a specific project.
        
        Args:
            project_id: The ID of the project to retrieve
            
        Returns:
            JSON object with project details including id, name, 
            description, created_at, and updated_at.
        """
        response = httpx.get(f"{get_api_base()}/projects/{project_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def create_project(name: str, description: str = "") -> str:
        """Create a new BlueWriter project.
        
        Args:
            name: The name for the new project (required)
            description: Optional description for the project
            
        Returns:
            JSON object with the created project details.
        """
        response = httpx.post(
            f"{get_api_base()}/projects",
            json={"name": name, "description": description}
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def update_project(
        project_id: int, 
        name: str = None, 
        description: str = None
    ) -> str:
        """Update an existing project's name or description.
        
        Args:
            project_id: The ID of the project to update
            name: New name for the project (optional)
            description: New description for the project (optional)
            
        Returns:
            JSON object with the updated project details.
        """
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        
        response = httpx.put(
            f"{get_api_base()}/projects/{project_id}",
            json=data
        )
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def delete_project(project_id: int) -> str:
        """Delete a project and all its contents.
        
        WARNING: This permanently deletes the project and all its 
        stories, chapters, and encyclopedia entries.
        
        Args:
            project_id: The ID of the project to delete
            
        Returns:
            Confirmation message.
        """
        response = httpx.delete(f"{get_api_base()}/projects/{project_id}")
        response.raise_for_status()
        return response.text
    
    @mcp.tool()
    def open_project(project_id: int) -> str:
        """Open/select a project in the BlueWriter UI.
        
        This will load the project in BlueWriter's interface,
        showing its stories in the sidebar.
        
        Args:
            project_id: The ID of the project to open
            
        Returns:
            Confirmation message.
        """
        response = httpx.post(f"{get_api_base()}/projects/{project_id}/open")
        response.raise_for_status()
        return response.text
