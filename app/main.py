"""
Main entry point for the iROILS Evaluations application.

This module initializes the application components and routes to the
appropriate page based on the command-line arguments.
"""

import argparse
import logging
import os
import sys
from typing import Dict, Any, Optional

import streamlit as st

from app.config import config
from app.services.auth_service import AuthService
from app.services.database_service import DatabaseService
from app.utils.network_utils import NetworkResolver


def setup_logging() -> None:
    """Set up application logging."""
    # Get logging configuration
    logging_config = config.get_logging_config()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, logging_config['level']),
        format=logging_config['format'],
        filename=logging_config['file'] if logging_config['file'] else None
    )
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")


def initialize_services() -> Dict[str, Any]:
    """
    Initialize application services.
    
    Returns:
        Dict[str, Any]: Dictionary of initialized services
    """
    logger = logging.getLogger(__name__)
    
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


def run_admin_page(services: Dict[str, Any]) -> None:
    """
    Run the admin dashboard.
    
    Args:
        services (Dict[str, Any]): Dictionary of application services
    """
    from app.pages.admin_page import AdminPage
    
    admin_page = AdminPage(
        auth_service=services['auth_service'],
        db_service=services['db_service']
    )
    admin_page.render()


def run_submission_page(services: Dict[str, Any]) -> None:
    """
    Run the evaluator submission page.
    
    Args:
        services (Dict[str, Any]): Dictionary of application services
    """
    from app.pages.submission_page import SubmissionPage
    
    submission_page = SubmissionPage(
        auth_service=services['auth_service'],
        db_service=services['db_service']
    )
    submission_page.render()


def run_dashboard_page(services: Dict[str, Any]) -> None:
    """
    Run the PostgreSQL dashboard page.
    
    Args:
        services (Dict[str, Any]): Dictionary of application services
    """
    from app.pages.dashboard_page import DashboardPage
    
    dashboard_page = DashboardPage(
        auth_service=services['auth_service'],
        db_service=services['db_service']
    )
    dashboard_page.render()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="iROILS Evaluations Application")
    
    parser.add_argument(
        '--page', 
        type=str, 
        choices=['admin', 'submission', 'dashboard'],
        default='admin',
        help='Page to run'
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=None,
        help='Port to run the Streamlit server on'
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting iROILS Evaluations Application")
    
    # Parse arguments
    args = parse_arguments()
    
    # Initialize services
    try:
        services = initialize_services()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        sys.exit(1)
    
    # Set Streamlit page configuration
    st.set_page_config(
        page_title="iROILS Evaluations",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply custom CSS
    css_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Route to the appropriate page
    if args.page == 'admin':
        run_admin_page(services)
    elif args.page == 'submission':
        run_submission_page(services)
    elif args.page == 'dashboard':
        run_dashboard_page(services)
    else:
        logger.error(f"Unknown page: {args.page}")
        st.error(f"Unknown page: {args.page}")


if __name__ == "__main__":
    main()