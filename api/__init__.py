"""
BlueWriter REST API Package.

Provides a REST API for controlling BlueWriter programmatically.
Used by the MCP server and can be used by other clients.
"""
from api.server import create_app, run_server

__all__ = ['create_app', 'run_server']
