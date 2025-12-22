"""
BlueWriter REST API Server.

Creates and configures the FastAPI application for BlueWriter.
The API server runs in a background thread when BlueWriter starts.
"""
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app(services: Dict[str, Any]) -> FastAPI:
    """Create and configure the FastAPI application.
    
    Args:
        services: Dictionary of service instances:
            - 'project': ProjectService
            - 'story': StoryService
            - 'chapter': ChapterService
            - 'encyclopedia': EncyclopediaService
            - 'canvas': CanvasService
            - 'editor': EditorService
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="BlueWriter API",
        description="REST API for BlueWriter fiction writing application",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS for local development and external clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store services in app state for dependency injection
    app.state.services = services
    
    # Register routes
    from api.routes import projects, stories, chapters, encyclopedia, canvas, state
    
    app.include_router(projects.router, prefix="/projects", tags=["Projects"])
    app.include_router(stories.router, tags=["Stories"])
    app.include_router(chapters.router, tags=["Chapters"])
    app.include_router(encyclopedia.router, tags=["Encyclopedia"])
    app.include_router(canvas.router, tags=["Canvas"])
    app.include_router(state.router, prefix="/state", tags=["State"])
    
    @app.get("/", tags=["Health"])
    async def root():
        """API root - health check."""
        return {
            "status": "ok",
            "app": "BlueWriter API",
            "version": "1.0.0",
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


def run_server(
    app: FastAPI,
    host: str = "127.0.0.1",
    port: int = 5000,
    log_level: str = "warning",
) -> None:
    """Run the API server (blocking).
    
    This should be called from a background thread.
    
    Args:
        app: FastAPI application instance
        host: Host to bind to (default: localhost only)
        port: Port to listen on (default: 5000)
        log_level: Uvicorn log level (default: warning)
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level=log_level)


__all__ = ['create_app', 'run_server']
