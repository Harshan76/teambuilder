import os
import sys
import pytest
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import TestConfig
from database.db import db_manager, Base
from database.seed_data import seed_database
from app import create_app

@pytest.fixture(scope="session")
def app():
    """Create Flask application configured for testing with in-memory SQLite."""
    application = create_app(TestConfig)
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    return application

@pytest.fixture(scope="function")
def db_session(app):
    """Provides a fresh, seeded database session for each test function."""
    db_manager.init_db(uri_override="sqlite:///:memory:")
    Base.metadata.drop_all(db_manager.engine)
    Base.metadata.create_all(db_manager.engine)
    
    session = db_manager.get_session()
    seed_database(session=session)
    
    yield session
    
    session.close()

@pytest.fixture
def client(app, db_session):
    """Flask test client."""
    return app.test_client()
