"""
Main entry point for the unified iROILS Evaluations application.

This module initializes the Streamlit application and handles routing
between different pages through a unified interface.
"""

import streamlit as st
import logging
import sys
import os
import time

# Add the parent directory to sys.path to resolve import issues
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.session import SessionState
from app.config.config_manager import ConfigManager
from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService
from app.pages.admin_page import AdminPage
from app.pages.submission_page import SubmissionPage
from app.pages.overview_page import OverviewPage
from app.pages.analysis_page import AnalysisPage
from app.pages.selection_page import SelectionPage
from app.pages.tag_dashboard_page import TagDashboardPage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize session state
from app.core.session import get_session_state
if 'session' not in st.session_state:
    st.session_state.session = get_session_state(st.session_state)
    
# Initialize authentication-related session variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'last_activity' not in st.session_state:
    st.session_state['last_activity'] = time.time()
if 'evaluator_logged_in' not in st.session_state:
    st.session_state['evaluator_logged_in'] = False
if 'evaluator_username' not in st.session_state:
    st.session_state['evaluator_username'] = None
if 'evaluator_institution' not in st.session_state:
    st.session_state['evaluator_institution'] = None
if 'institution' not in st.session_state:
    st.session_state['institution'] = None

def main():
    """Main function to run the unified Streamlit application."""
    
    # Set page config
    st.set_page_config(
        page_title="iROILS Evaluations Suite",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Hide default Streamlit sidebar menu
    hide_streamlit_elements = """
        <style>
            #MainMenu {visibility: hidden;}
            div[data-testid="stSidebarNav"] {display: none;}
            footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_elements, unsafe_allow_html=True)
    
    # Load custom CSS
    css_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Initialize config
    config = ConfigManager()
    
    # Initialize services
    db_config = config.get_postgresql_config()
    db_service = DatabaseService(
        host=db_config['host'],
        port=int(db_config['port']),
        user=db_config['user'],
        password=db_config['password'],
        dbname=db_config['dbname']
    )
    
    auth_service = AuthService()
    session = st.session_state.session
    
    # Create sidebar navigation
    st.sidebar.title("iROILS Evaluations")
    
    # User authentication
    if not session.get('authenticated', False):
        with st.sidebar:
            st.header("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                try:
                    # Try admin authentication first
                    if auth_service.authenticate_admin(username, password):
                        # Both session state systems
                        # Main session system
                        session.set('authenticated', True)
                        session.set('username', username)
                        session.set('user_role', 'admin')
                        
                        # For SecurePage compatibility
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.session_state['user_role'] = 'admin'
                        st.session_state['last_activity'] = time.time()
                        
                        st.success("Successfully logged in as administrator!")
                        st.rerun()
                        
                    # If admin authentication fails, try evaluator authentication
                    elif institution := auth_service.authenticate_evaluator(username, password):
                        # Main session system
                        session.set('authenticated', True)
                        session.set('username', username)
                        session.set('user_role', 'evaluator')
                        session.set('institution', institution)
                        session.set('evaluator_institution', institution)  # Required by SubmissionPage
                        
                        # For SecurePage compatibility
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.session_state['user_role'] = 'evaluator'
                        st.session_state['last_activity'] = time.time()
                        st.session_state['evaluator_logged_in'] = True
                        st.session_state['evaluator_username'] = username
                        st.session_state['evaluator_institution'] = institution
                        st.session_state['institution'] = institution
                        
                        st.success(f"Successfully logged in as evaluator for {institution}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
    
    else:
        # Welcome message and logout option
        st.sidebar.write(f"Welcome, {session.get('username')}!")
        if st.sidebar.button("Logout"):
            # Clear both session state systems
            # Main session system
            session.set('authenticated', False)
            session.set('username', None)
            session.set('user_role', None)
            session.set('institution', None)
            session.set('evaluator_institution', None)
            
            # For SecurePage compatibility
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.session_state['user_role'] = None
            st.session_state['last_activity'] = time.time()
            st.session_state['evaluator_logged_in'] = False
            st.session_state['evaluator_username'] = None
            st.session_state['evaluator_institution'] = None
            st.session_state['institution'] = None
            
            st.rerun()
        
        # Navigation options
        st.sidebar.header("Navigation")
        user_role = session.get('user_role')
        
        # Create role-appropriate navigation options
        if user_role == "admin":
            page_options = [
                "Overview",
                "Admin Dashboard", 
                "Data Analysis", 
                "Tag Analysis", 
                "User Submission"
            ]
        else:  # evaluator role
            page_options = [
                "Overview",
                "User Submission"
            ]
        
        selected_page = st.sidebar.radio("Select Page", page_options, key="nav_radio")
        
        # Institution selection
        institutions = ["UAB", "MBPCC"]
        selected_institution = st.sidebar.selectbox(
            "Select Institution", institutions, key='global_institution_select'
        )
        
        # Render the selected page
        try:
            if selected_page == "Admin Dashboard":
                if user_role == "admin":
                    admin_page = AdminPage(auth_service, db_service)
                    admin_page.render()
                else:
                    st.error("You need administrator privileges to access this page.")
                    
            elif selected_page == "Data Analysis":
                if user_role == "admin":
                    analysis_page = AnalysisPage(db_service, selected_institution)
                    analysis_page.render()
                else:
                    st.error("You need administrator privileges to access this page.")
                    
            elif selected_page == "Tag Analysis":
                if user_role == "admin":
                    dashboard_page = TagDashboardPage(db_service, selected_institution)
                    dashboard_page.render()
                else:
                    st.error("You need administrator privileges to access this page.")
                    
            elif selected_page == "User Submission":
                # Import here to avoid forward reference issues
                from app.pages.submission_page import SubmissionPage
                
                # For evaluators, use their role
                if user_role == "evaluator":
                    submission_page = SubmissionPage(auth_service, db_service)
                    submission_page.render()
                # For admins, don't enforce evaluator role requirement
                else:
                    # Create a subclass that overrides the required_role check
                    class AdminSubmissionPage(SubmissionPage):
                        def __init__(self, auth_service, db_service):
                            # Initialize without role restriction
                            super().__init__(auth_service, db_service)
                            self.required_role = None  # Override the required role
                    
                    # Render the modified page
                    admin_submission_page = AdminSubmissionPage(auth_service, db_service)
                    admin_submission_page.render()
                
            elif selected_page == "Overview":
                overview_page = OverviewPage(auth_service, db_service)
                overview_page.render()
                
        except Exception as e:
            st.error(f"Error rendering page: {str(e)}")
            logging.error(f"Error rendering page {selected_page}: {str(e)}", exc_info=True)
            
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("iROILS Evaluations v1.0.0")

if __name__ == "__main__":
    main()