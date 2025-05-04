"""Unit tests for the AuthService class."""

import time
import pytest
from unittest.mock import patch

from app.exceptions.auth_exceptions import InvalidCredentialsError, UnauthorizedAccessError
from app.services.auth_service import AuthService
from app.models.user import AdminUser, EvaluatorUser


class TestAuthService:
    """Tests for the AuthService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.auth_service = AuthService(session_timeout=900)
        
        # Admin credentials for testing
        self.valid_admin = {'username': 'iroils', 'password': 'iROILS'}
        self.invalid_admin = {'username': 'admin', 'password': 'wrong'}
        
        # Evaluator credentials for testing
        self.valid_evaluator = {'username': 'aalexandrian', 'password': '1232'}
        self.invalid_evaluator = {'username': 'evaluator', 'password': 'wrong'}
    
    def test_authenticate_admin(self):
        """Test authenticating an admin user."""
        # Test valid admin
        result = self.auth_service.authenticate_admin(
            self.valid_admin['username'], 
            self.valid_admin['password']
        )
        assert result is True
        
        # Test invalid admin
        result = self.auth_service.authenticate_admin(
            self.invalid_admin['username'], 
            self.invalid_admin['password']
        )
        assert result is False
    
    def test_authenticate_evaluator(self):
        """Test authenticating an evaluator user."""
        # Test valid evaluator
        result = self.auth_service.authenticate_evaluator(
            self.valid_evaluator['username'], 
            self.valid_evaluator['password']
        )
        assert result == 'UAB'
        
        # Test invalid evaluator
        result = self.auth_service.authenticate_evaluator(
            self.invalid_evaluator['username'], 
            self.invalid_evaluator['password']
        )
        assert result is None
    
    def test_login_admin(self):
        """Test logging in as an admin."""
        # Test valid admin login
        session_state = {}
        user = self.auth_service.login(
            session_state, 
            self.valid_admin['username'], 
            self.valid_admin['password']
        )
        
        # Verify returned user
        assert isinstance(user, AdminUser)
        assert user.username == self.valid_admin['username']
        assert user.role == 'admin'
        
        # Verify session state
        assert session_state['logged_in'] is True
        assert session_state['user_role'] == 'admin'
        assert session_state['username'] == self.valid_admin['username']
        assert 'last_activity' in session_state
    
    def test_login_evaluator(self):
        """Test logging in as an evaluator."""
        # Test valid evaluator login
        session_state = {}
        user = self.auth_service.login(
            session_state, 
            self.valid_evaluator['username'], 
            self.valid_evaluator['password']
        )
        
        # Verify returned user
        assert isinstance(user, EvaluatorUser)
        assert user.username == self.valid_evaluator['username']
        assert user.role == 'evaluator'
        assert user.institution == 'UAB'
        
        # Verify session state
        assert session_state['logged_in'] is True
        assert session_state['user_role'] == 'evaluator'
        assert session_state['username'] == self.valid_evaluator['username']
        assert session_state['evaluator_logged_in'] is True
        assert session_state['evaluator_username'] == self.valid_evaluator['username']
        assert session_state['evaluator_institution'] == 'UAB'
        assert 'last_activity' in session_state
    
    def test_login_invalid(self):
        """Test login with invalid credentials."""
        # Test invalid login
        session_state = {}
        with pytest.raises(InvalidCredentialsError):
            self.auth_service.login(
                session_state, 
                self.invalid_admin['username'], 
                self.invalid_admin['password']
            )
    
    def test_logout(self):
        """Test logging out."""
        # Set up session state
        session_state = {
            'logged_in': True,
            'user_role': 'admin',
            'username': 'admin',
            'last_activity': time.time(),
            'evaluator_logged_in': True,
            'evaluator_username': 'admin',
            'evaluator_institution': 'UAB'
        }
        
        # Logout
        self.auth_service.logout(session_state)
        
        # Verify session state was cleared
        assert 'logged_in' not in session_state
        assert 'user_role' not in session_state
        assert 'username' not in session_state
        assert 'last_activity' not in session_state
        assert 'evaluator_logged_in' not in session_state
        assert 'evaluator_username' not in session_state
        assert 'evaluator_institution' not in session_state
    
    def test_check_session_timeout(self):
        """Test checking session timeout."""
        # Set up session state with fresh timestamp
        session_state = {'last_activity': time.time()}
        
        # Check timeout (should not timeout)
        result = self.auth_service.check_session_timeout(session_state)
        assert result is False
        
        # Set up session state with expired timestamp
        expired_time = time.time() - 1000  # 1000 seconds ago (> 900 timeout)
        session_state = {'last_activity': expired_time}
        
        # Check timeout (should timeout)
        result = self.auth_service.check_session_timeout(session_state)
        assert result is True
        
        # Verify session state was cleared on timeout
        assert 'last_activity' not in session_state
    
    def test_get_current_user(self):
        """Test getting the current user from session state."""
        # Set up admin session state
        admin_session = {
            'logged_in': True,
            'user_role': 'admin',
            'username': 'admin',
            'last_activity': time.time()
        }
        
        # Get admin user
        user = self.auth_service.get_current_user(admin_session)
        assert isinstance(user, AdminUser)
        assert user.username == 'admin'
        assert user.role == 'admin'
        
        # Set up evaluator session state
        evaluator_session = {
            'logged_in': True,
            'user_role': 'evaluator',
            'username': 'evaluator',
            'evaluator_institution': 'UAB',
            'last_activity': time.time()
        }
        
        # Get evaluator user
        user = self.auth_service.get_current_user(evaluator_session)
        assert isinstance(user, EvaluatorUser)
        assert user.username == 'evaluator'
        assert user.role == 'evaluator'
        assert user.institution == 'UAB'
        
        # Test with no user logged in
        empty_session = {}
        user = self.auth_service.get_current_user(empty_session)
        assert user is None
    
    def test_require_login(self):
        """Test requiring login."""
        # Set up logged in session
        logged_in_session = {
            'logged_in': True,
            'user_role': 'admin',
            'username': 'admin',
            'last_activity': time.time()
        }
        
        # Should return user without error
        user = self.auth_service.require_login(logged_in_session)
        assert user is not None
        
        # Test with no user logged in
        empty_session = {}
        with pytest.raises(UnauthorizedAccessError):
            self.auth_service.require_login(empty_session)
    
    def test_require_role(self):
        """Test requiring a specific role."""
        # Set up admin session
        admin_session = {
            'logged_in': True,
            'user_role': 'admin',
            'username': 'admin',
            'last_activity': time.time()
        }
        
        # Should return user for correct role
        user = self.auth_service.require_role(admin_session, 'admin')
        assert user is not None
        
        # Should raise error for incorrect role
        with pytest.raises(UnauthorizedAccessError):
            self.auth_service.require_role(admin_session, 'evaluator')
        
        # Test with no user logged in
        empty_session = {}
        with pytest.raises(UnauthorizedAccessError):
            self.auth_service.require_role(empty_session, 'admin')