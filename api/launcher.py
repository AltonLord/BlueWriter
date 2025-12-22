"""
BlueWriter API Server Launcher.

Utilities for starting the REST API server in a background thread.
"""
import threading
from typing import Dict, Any, Optional

from fastapi import FastAPI


_server_thread: Optional[threading.Thread] = None
_app: Optional[FastAPI] = None


def start_api_server(
    services: Dict[str, Any],
    host: str = "127.0.0.1",
    port: int = 5000,
) -> threading.Thread:
    """Start the BlueWriter API server in a background thread.
    
    Args:
        services: Dictionary of service instances
        host: Host to bind to (default: localhost only)
        port: Port to listen on (default: 5000)
    
    Returns:
        The background thread running the server
    """
    global _server_thread, _app
    
    from api.server import create_app, run_server
    
    _app = create_app(services)
    
    def run():
        run_server(_app, host=host, port=port, log_level="warning")
    
    _server_thread = threading.Thread(
        target=run,
        name="BlueWriterAPIServer",
        daemon=True,  # Dies when main app exits
    )
    _server_thread.start()
    
    return _server_thread


def get_api_url(port: int = 5000) -> str:
    """Get the URL where the API is running."""
    return f"http://127.0.0.1:{port}"


def is_server_running() -> bool:
    """Check if the API server thread is running."""
    global _server_thread
    return _server_thread is not None and _server_thread.is_alive()


__all__ = ['start_api_server', 'get_api_url', 'is_server_running']
