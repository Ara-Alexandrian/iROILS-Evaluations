"""
Page components for the iROILS Evaluations application.

This package provides the Streamlit page components for the application.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import streamlit as st

from app.core.session import SessionState
from app.models.user import User
from app.services.auth_service import AuthService


class BasePage(ABC):
    """
    Base class for all page components.
    
    This abstract class defines the common interface and functionality
    for all page components in the application.
    """
    
    def __init__(self, title: str):
        """
        Initialize the page.
        
        Args:
            title (str): The page title
        """
        self.title = title
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.session = SessionState(st.session_state)
    
    def render(self) -> None:
        """
        Render the page.
        
        This method handles common page rendering tasks like setting the title
        and providing a consistent structure.
        """
        st.title(self.title)
        
        # Delegate to the specific page implementation
        self._render_content()
    
    @abstractmethod
    def _render_content(self) -> None:
        """
        Render the page content.
        
        This abstract method must be implemented by subclasses to provide
        the specific content for each page.
        """
        pass
    

class SecurePage(BasePage):
    """
    Base class for pages that require authentication.
    
    This class extends BasePage to add authentication checks
    and access control.
    """
    
    def __init__(self, title: str, auth_service: AuthService, required_role: Optional[str] = None):
        """
        Initialize the secure page.
        
        Args:
            title (str): The page title
            auth_service (AuthService): The authentication service
            required_role (Optional[str]): Required role for access (None for any authenticated user)
        """
        super().__init__(title)
        self.auth_service = auth_service
        self.required_role = required_role
    
    def render(self) -> None:
        """
        Render the page with authentication checks.
        """
        st.title(self.title)
        
        # Check both session state methods for logged in status
        logged_in = self.session.get('logged_in', False) or st.session_state.get('logged_in', False)
        
        if not logged_in:
            self._render_login_form()
        else:
            # Check if session has timed out
            if self.auth_service.check_session_timeout(st.session_state):
                st.warning("Your session has expired. Please log in again.")
                self._render_login_form()
                return
            
            # Check role requirements if specified
            user_role = self.session.get('user_role') or st.session_state.get('user_role')
            if self.required_role and user_role != self.required_role:
                # Only show error if the role check is enforced (not overridden)
                st.error(f"Access denied: {self.required_role} role required.")
                
                # Add a return to main menu button
                if st.button("Return to Main Menu", key=f"return_to_main_{self.title}"):
                    # Clear the current page selection
                    st.session_state['nav_radio'] = "Overview"
                    st.rerun()
                    
                self._render_logout_button()
                return
            
            # Render page content
            self._render_content()
            
            # Render a return button at the bottom of the page
            if st.button("Return to Main Menu", key=f"return_button_{self.title}"):
                # Clear the current page selection
                st.session_state['nav_radio'] = "Overview"
                st.rerun()
            
            # Always render logout button
            self._render_logout_button()
    
    def _render_login_form(self) -> None:
        """
        Render the login form.
        """
        st.markdown("## Login")
        
        # Wrap inputs inside a form to enable 'Enter' key submission
        with st.form(key="login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button(label="Login")
        
        # Process form submission
        if submit_button:
            try:
                # Try admin authentication first
                if self.auth_service.authenticate_admin(username, password):
                    # Update session state for admin
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['user_role'] = 'admin'
                    st.session_state['last_activity'] = time.time()
                    
                    st.success(f"Welcome, {username} (Administrator)!")
                    st.rerun()  # Refresh the page
                
                # Try evaluator authentication if admin auth fails
                elif institution := self.auth_service.authenticate_evaluator(username, password):
                    # Update session state for evaluator
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['user_role'] = 'evaluator'
                    st.session_state['last_activity'] = time.time()
                    st.session_state['evaluator_logged_in'] = True
                    st.session_state['evaluator_username'] = username
                    st.session_state['evaluator_institution'] = institution
                    st.session_state['institution'] = institution
                    
                    st.success(f"Welcome, {username} (Evaluator for {institution})!")
                    st.rerun()  # Refresh the page
                
                else:
                    st.error("Invalid username or password")
            
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
    
    def _render_logout_button(self) -> None:
        """
        Render the logout button.
        """
        # Generate a unique key for the logout button based on the page title
        button_key = f"logout_button_{self.title.replace(' ', '_').lower()}"
        if st.button("Logout", key=button_key):
            self.auth_service.logout(st.session_state)
            st.rerun()  # Refresh the page