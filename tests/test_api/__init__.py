"""API test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.server import create_app


@pytest.fixture
def api_client(all_services) -> TestClient:
    """Create a FastAPI TestClient with all services.
    
    Uses the all_services fixture which provides services
    connected to a test database.
    """
    app = create_app(all_services)
    return TestClient(app)
