import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.db.session import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Initialize database schema before running test session.
    """
    init_db()


@pytest.fixture
def client():
    """
    TestClient fixture for making API requests.
    """
    with TestClient(app) as test_client:
        yield test_client
