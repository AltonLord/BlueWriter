"""
API Server startup utilities for BlueWriter.

Provides functions to start the REST API server in a background thread.
"""
import threading
from typing import Dict, Any, Optional

from api.server import create_app


_api_thread: Optional[threading.Thread] = None
_api_app = None


def start_api_server(
    services: Dict[str, Any],
    host: str = "127.0.0.1",
    port: int = 5000,
) -> threading.Thread:
    """Start the API server in a background thread.
    
    Args:
        services: Dictionary of service instances
        host: Host to bind to (default: localhost only)
        port: Port to listen on (default: 5000)
        
    Returns:
        The background thread running the server
    """
    global _api_thread, _api_app
    
    # Create the FastAPI app
    _api_app = create_app(services)
    
    def run_server():
        import uvicorn
        # Use log_level="error" to reduce noise
        uvicorn.run(_api_app, host=host, port=port, log_level="error")
    
    # Start in daemon thread (dies when main app exits)
    _api_thread = threading.Thread(target=run_server, daemon=True)
    _api_thread.start()
    
    return _api_thread


def get_api_thread() -> Optional[threading.Thread]:
    """Get the API server thread if running."""
    return _api_thread


def is_api_running() -> bool:
    """Check if the API server is running."""
    return _api_thread is not None and _api_thread.is_alive()


__all__ = ['start_api_server', 'get_api_thread', 'is_api_running']
