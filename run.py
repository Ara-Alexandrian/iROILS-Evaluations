#!/usr/bin/env python3
"""
Launcher script for the iROILS Evaluations application.

This script launches all application components in separate processes.
"""

import subprocess
import os
import sys
import signal
import logging
from typing import List, Dict, Any


# Configuration
APP_PAGES = [
    {
        'name': 'Admin Dashboard',
        'script': os.path.join(os.path.dirname(__file__), 'app', 'main_v2.py'),
        'port': 8501
    },
    {
        'name': 'Evaluator Dashboard',
        'script': os.path.join(os.path.dirname(__file__), 'app', 'submissions_v2.py'),
        'port': 8502
    },
    {
        'name': 'Database Dashboard',
        'script': os.path.join(os.path.dirname(__file__), 'app', 'dashboard_v2.py'),
        'port': 8503
    }
]

# Global variables
processes = []


def setup_logging() -> logging.Logger:
    """
    Set up logging.
    
    Returns:
        logging.Logger: Logger instance
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def start_app(script_path: str, port: int) -> subprocess.Popen:
    """
    Start a Streamlit app process.
    
    Args:
        script_path (str): Path to the script to run
        port (int): Port to run on
        
    Returns:
        subprocess.Popen: Process object
    """
    python_executable = sys.executable
    
    # Construct command
    cmd = [
        python_executable,
        '-m', 'streamlit', 'run', script_path,
        '--server.port', str(port)
    ]
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    return process


def start_all_apps(logger: logging.Logger) -> None:
    """
    Start all application components.
    
    Args:
        logger (logging.Logger): Logger instance
    """
    global processes
    
    for app in APP_PAGES:
        logger.info(f"Starting {app['name']} on port {app['port']}")
        process = start_app(app['script'], app['port'])
        processes.append(process)
        logger.info(f"{app['name']} started with PID {process.pid}")


def cleanup(logger: logging.Logger) -> None:
    """
    Clean up processes on exit.
    
    Args:
        logger (logging.Logger): Logger instance
    """
    global processes
    
    logger.info("Shutting down all processes...")
    
    for process in processes:
        if process.poll() is None:  # Process is still running
            logger.info(f"Terminating process with PID {process.pid}")
            process.terminate()
    
    # Give processes time to terminate gracefully
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"Process with PID {process.pid} did not terminate gracefully, killing...")
            process.kill()
    
    logger.info("All processes terminated")


def signal_handler(sig, frame) -> None:
    """
    Handle termination signals.
    
    Args:
        sig: Signal number
        frame: Current stack frame
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {sig}")
    cleanup(logger)
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting iROILS Evaluations Application")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all application components
        start_all_apps(logger)
        
        # Print information
        logger.info("All applications started successfully:")
        for app in APP_PAGES:
            logger.info(f"- {app['name']}: http://localhost:{app['port']}")
        logger.info("Press Ctrl+C to exit")
        
        # Keep main process running
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        cleanup(logger)


if __name__ == "__main__":
    main()