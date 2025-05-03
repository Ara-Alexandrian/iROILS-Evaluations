"""
Authentication service for the iROILS Evaluations application.

This module provides authentication and session management functionality,
including user login, session tracking, and timeout handling.
"""

import time
import logging
from typing import Dict, Any, Optional, Union, cast

from app.models.user import User, AdminUser, EvaluatorUser, UserRole
from app.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    SessionExpiredError,
    UnauthorizedAccessError
)

class AuthService:
    """
    Service for user authentication and session management.
    
    This class handles user authentication, session state management,
    and session timeout tracking.
    """
    
    def __init__(self, session_timeout: int = 900):
        """
        Initialize the authentication service.
        
        Args:
            session_timeout (int): Session timeout in seconds (default: 15 minutes)
        """
        self.logger = logging.getLogger(__name__)
        self.session_timeout = session_timeout
        
        # Admin credentials
        self.admin_credentials = {
            'iroils': 'iROILS'
        }
        
        # Evaluator credentials mapped to their respective institutions
        self.evaluator_credentials = {
            'astam': {'password': 'A3nR6yP7', 'institution': 'MBPCC'},
            'kkirby': {'password': 'K4wT9bQ1', 'institution': 'MBPCC'},
            'dsolis': {'password': 'T2hP6vC4', 'institution': 'MBPCC'},
            'gpitcher': {'password': 'B3kN9wL5', 'institution': 'MBPCC'},
            'jashford': {'password': 'P6vT8mJ2', 'institution': 'MBPCC'},
            'hspears': {'password': 'R4xB2gW9', 'institution': 'MBPCC'},
            'aalexandrian': {'password': '1232', 'institution': 'UAB'},
            'nviscariello': {'password': 'L8kY5nJ3', 'institution': 'UAB'},
            'rsullivan': {'password': 'C7bM5nW2', 'institution': 'UAB'},
            'jbelliveau': {'password': 'F3rP6yV8', 'institution': 'UAB'},
            'apdalton': {'password': 'G5tV2cQ9', 'institution': 'UAB'},
        }
    
    def authenticate_admin(self, username: str, password: str) -> bool:
        """
        Authenticate an admin user.
        
        Args:
            username (str): Admin username
            password (str): Admin password
            
        Returns:
            bool: True if authentication succeeds, False otherwise
        """
        if username in self.admin_credentials and self.admin_credentials[username] == password:
            self.logger.info(f"Admin user {username} authenticated successfully")
            return True
        
        self.logger.warning(f"Failed admin authentication attempt for user {username}")
        return False
    
    def authenticate_evaluator(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate an evaluator user.
        
        Args:
            username (str): Evaluator username
            password (str): Evaluator password
            
        Returns:
            Optional[str]: The evaluator's institution if authentication succeeds, None otherwise
        """
        evaluator_data = self.evaluator_credentials.get(username)
        
        if evaluator_data and evaluator_data['password'] == password:
            self.logger.info(f"Evaluator {username} authenticated successfully for institution {evaluator_data['institution']}")
            return evaluator_data['institution']
        
        self.logger.warning(f"Failed evaluator authentication attempt for user {username}")
        return None
    
    def login(self, session_state: Dict[str, Any], username: str, password: str) -> User:
        """
        Authenticate a user (admin or evaluator) and update the session state.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
            username (str): The username to authenticate
            password (str): The password to verify
            
        Returns:
            User: The authenticated user object
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        # Try admin authentication first
        if self.authenticate_admin(username, password):
            user = AdminUser(username)
            self._update_session_state(session_state, user)
            return user
        
        # If admin authentication fails, try evaluator authentication
        institution = self.authenticate_evaluator(username, password)
        if institution:
            user = EvaluatorUser(username, institution)
            self._update_session_state(session_state, user)
            return user
        
        # If both fail, raise an exception
        raise InvalidCredentialsError(username)
    
    def _update_session_state(self, session_state: Dict[str, Any], user: User) -> None:
        """
        Update the session state with user information.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
            user (User): The authenticated user
        """
        # Common session state updates
        session_state['logged_in'] = True
        session_state['user_role'] = user.role
        session_state['username'] = user.username
        session_state['last_activity'] = time.time()
        
        # Role-specific session state updates
        if user.role == 'evaluator':
            evaluator_user = cast(EvaluatorUser, user)
            session_state['evaluator_logged_in'] = True
            session_state['evaluator_username'] = evaluator_user.username
            session_state['evaluator_institution'] = evaluator_user.institution
    
    def logout(self, session_state: Dict[str, Any]) -> None:
        """
        Log the current user out by clearing the session state.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
        """
        # Clear all authentication-related session state
        session_state.pop('logged_in', None)
        session_state.pop('user_role', None)
        session_state.pop('username', None)
        session_state.pop('last_activity', None)
        
        # Clear evaluator-specific session state
        session_state.pop('evaluator_logged_in', None)
        session_state.pop('evaluator_username', None)
        session_state.pop('evaluator_institution', None)
        
        self.logger.info("User logged out successfully")
    
    def check_session_timeout(self, session_state: Dict[str, Any]) -> bool:
        """
        Check if the user session has timed out and update the last activity timestamp.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
            
        Returns:
            bool: True if the session has timed out, False otherwise
        """
        if 'last_activity' in session_state:
            current_time = time.time()
            elapsed_time = current_time - session_state['last_activity']
            
            if elapsed_time > self.session_timeout:
                self.logger.info("Session timed out due to inactivity")
                self.logout(session_state)
                return True
            else:
                # Update last activity timestamp
                session_state['last_activity'] = current_time
        
        return False
    
    def get_current_user(self, session_state: Dict[str, Any]) -> Optional[User]:
        """
        Get the current logged-in user from the session state.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
            
        Returns:
            Optional[User]: The current user or None if no user is logged in
        """
        if not session_state.get('logged_in', False):
            return None
        
        # Check if the session has timed out
        if self.check_session_timeout(session_state):
            return None
        
        # Get user information from session state
        role = session_state.get('user_role')
        username = session_state.get('username')
        
        if not role or not username:
            return None
        
        # Create the appropriate user object based on role
        if role == 'admin':
            return AdminUser(username)
        elif role == 'evaluator':
            institution = session_state.get('evaluator_institution')
            if institution:
                return EvaluatorUser(username, institution)
        
        return None
    
    def require_login(self, session_state: Dict[str, Any]) -> User:
        """
        Require that a user is logged in and return the user object.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
            
        Returns:
            User: The current logged-in user
            
        Raises:
            UnauthorizedAccessError: If no user is logged in or the session has timed out
        """
        user = self.get_current_user(session_state)
        
        if not user:
            raise UnauthorizedAccessError(message="Login required to access this resource")
        
        return user
    
    def require_role(self, session_state: Dict[str, Any], required_role: UserRole) -> User:
        """
        Require that a user is logged in with a specific role.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
            required_role (UserRole): The required user role
            
        Returns:
            User: The current logged-in user with the required role
            
        Raises:
            UnauthorizedAccessError: If no user is logged in, the session has timed out,
                                    or the user doesn't have the required role
        """
        user = self.require_login(session_state)
        
        if user.role != required_role:
            raise UnauthorizedAccessError(
                username=user.username, 
                message=f"Access denied: {required_role} role required"
            )
        
        return user