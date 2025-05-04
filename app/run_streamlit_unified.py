"""
Unified Streamlit app runner for the iROILS Evaluations application.

This script launches a single Streamlit application that integrates all the
previously separate dashboards into one unified interface with navigation.
"""

import subprocess
import os
import sys

# Add the parent directory to sys.path to help with imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """Run the unified Streamlit application."""
    # Path to the main application entry point
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "main_unified.py")
    
    # Check if the file exists
    if not os.path.exists(app_path):
        print(f"Error: {app_path} does not exist.")
        return
    
    print(f"Starting Streamlit app from {app_path}")
    
    # Run the Streamlit application
    process = subprocess.run(
        ["streamlit", "run", app_path, "--server.port=8501"],
        check=True
    )
    
    return process.returncode

if __name__ == "__main__":
    main()