"""Test configuration and fixtures for the iROILS Evaluations application."""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Add application root to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    mock = MagicMock()
    
    # Configure PostgreSQL settings
    mock.get_postgresql_config.return_value = {
        'host': 'localhost',
        'port': 5432,
        'user': 'test_user',
        'password': 'test_password',
        'dbname': 'test_db'
    }
    
    # Configure application settings
    mock.get_application_config.return_value = {
        'session_timeout': 900,
        'default_institution': 'UAB'
    }
    
    # Configure logging settings
    mock.get_logging_config.return_value = {
        'level': 'INFO',
        'file': '',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
    
    return mock


@pytest.fixture
def mock_db_connection():
    """Create a mock database connection for testing."""
    mock = MagicMock()
    
    # Configure cursor
    cursor = MagicMock()
    mock.cursor.return_value.__enter__.return_value = cursor
    
    # Configure autocommit
    mock.autocommit = True
    
    return mock


@pytest.fixture
def mock_db_service(mock_db_connection):
    """Create a mock database service for testing."""
    mock = MagicMock()
    mock.connection = mock_db_connection
    
    # Configure entry methods
    mock.get_entries.return_value = []
    mock.get_entry.return_value = None
    
    # Configure evaluation methods
    mock.get_evaluation.return_value = None
    mock.get_evaluations_by_evaluator.return_value = []
    
    # Configure stats methods
    mock.get_institution_stats.return_value = {
        'cumulative_summary': 0,
        'cumulative_tag': 0,
        'total_evaluations': 0
    }
    
    return mock


@pytest.fixture
def mock_auth_service():
    """Create a mock authentication service for testing."""
    mock = MagicMock()
    
    # Configure authentication methods
    mock.authenticate_admin.return_value = False
    mock.authenticate_evaluator.return_value = None
    
    # Configure session methods
    mock.check_session_timeout.return_value = False
    
    return mock


@pytest.fixture
def mock_session_state():
    """Create a mock session state for testing."""
    return {}