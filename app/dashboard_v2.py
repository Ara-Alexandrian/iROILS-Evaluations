"""
Database dashboard page for the iROILS Evaluations application.

This module provides the entry point for the database dashboard interface.
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

import streamlit as st

from app.config import config
from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService
from app.utils.network_utils import NetworkResolver
from app.pages.dashboard_page import DashboardPage

# Initialize application services
def setup_app():
    """
    Set up application services and configuration.
    
    This function is called once per Streamlit session.
    It initializes all necessary services and configuration.
    
    Returns:
        Dict[str, Any]: Dictionary of initialized services
    """
    # Set up logging
    logging_config = config.get_logging_config()
    logging.basicConfig(
        level=getattr(logging, logging_config['level']),
        format=logging_config['format'],
        filename=logging_config['file'] if logging_config['file'] else None
    )
    logger = logging.getLogger(__name__)
    logger.info("Initializing iROILS Evaluations Application - Dashboard Interface")
    
    try:
        # Initialize network resolver
        resolver = NetworkResolver(config)
        
        # Determine environment
        local_ip = resolver.get_local_ip()
        environment = resolver.resolve_environment(local_ip)
        logger.info(f"Running in {environment} environment with IP {local_ip}")
        
        # Get database configuration
        pg_config = config.get_postgresql_config(environment)
        
        # Initialize database service
        db_service = DatabaseService(
            host=pg_config['host'],
            port=pg_config['port'],
            user=pg_config['user'],
            password=pg_config['password'],
            dbname=pg_config['dbname']
        )
        
        # Initialize authentication service
        app_config = config.get_application_config()
        auth_service = AuthService(session_timeout=app_config['session_timeout'])
        
        return {
            'db_service': db_service,
            'auth_service': auth_service,
            'environment': environment
        }
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        st.error(f"Failed to initialize application: {e}")
        return None

# Main application entry point
def main():
    """Main application entry point."""
    # Set page configuration
    st.set_page_config(
        page_title="iROILS Database Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Hide default pages from sidebar
    hide_pages = """
    <style>
    div[data-testid="collapsedControl"] {display: none}
    section[data-testid="stSidebar"] {display: none}
    </style>
    """
    st.markdown(hide_pages, unsafe_allow_html=True)
    
    # Apply custom CSS
    css_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Initialize services if not already initialized
    if 'services' not in st.session_state:
        st.session_state['services'] = setup_app()
    
    # Show error and exit if initialization failed
    if not st.session_state['services']:
        st.error("Application failed to initialize. Please check the logs for details.")
        return
    
    # Get services
    services = st.session_state['services']
    
    # Import and render the dashboard page
    dashboard_page = DashboardPage(
        auth_service=services['auth_service'],
        db_service=services['db_service']
    )
    dashboard_page.render()

if __name__ == "__main__":
    main()