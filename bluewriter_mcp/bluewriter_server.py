#!/usr/bin/env python3
"""
BlueWriter MCP Server.

Provides AI assistants with tools to control BlueWriter.
Communicates with BlueWriter via REST API on localhost:5000.

Usage:
    python -m bluewriter_mcp.bluewriter_server
    
    Or configure in Claude Desktop:
    {
        "mcpServers": {
            "bluewriter": {
                "command": "python",
                "args": ["-m", "bluewriter_mcp.bluewriter_server"],
                "cwd": "/fast/BlueWriter"
            }
        }
    }
"""
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

# Default API base URL - BlueWriter runs here when started
API_BASE = os.environ.get("BLUEWRITER_API_URL", "http://127.0.0.1:5000")

# Create the MCP server
mcp = FastMCP(
    "bluewriter",
    instructions="""
BlueWriter is a fiction writing application with projects, stories, chapters, 
and an encyclopedia for world-building. Each project contains multiple stories, 
and each story contains chapters organized on a visual canvas.

Key concepts:
- Projects: Top-level containers for your writing
- Stories: Individual narratives within a project
- Chapters: Sections of a story, displayed as sticky notes on a canvas
- Encyclopedia: World-building reference entries (characters, locations, items, etc.)
- Canvas: Visual workspace where chapters are arranged as sticky notes
""",
)


def get_api_base() -> str:
    """Get the API base URL."""
    return API_BASE


# Import and register all tools
from bluewriter_mcp.tools.project_tools import register_project_tools
from bluewriter_mcp.tools.story_tools import register_story_tools
from bluewriter_mcp.tools.chapter_tools import register_chapter_tools
from bluewriter_mcp.tools.encyclopedia_tools import register_encyclopedia_tools
from bluewriter_mcp.tools.canvas_tools import register_canvas_tools

register_project_tools(mcp, get_api_base)
register_story_tools(mcp, get_api_base)
register_chapter_tools(mcp, get_api_base)
register_encyclopedia_tools(mcp, get_api_base)
register_canvas_tools(mcp, get_api_base)


if __name__ == "__main__":
    # Run the server via stdio (for Claude Desktop integration)
    mcp.run()
