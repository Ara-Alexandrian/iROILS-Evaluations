# app.py

import streamlit as st
import pandas as pd
from redis_manager import RedisManager, RedisSnapshotManager
from login_manager import LoginManager
from institution_manager import InstitutionManager
from network_resolver import NetworkResolver
from selection_page import SelectionPage
from overview_page import OverviewPage
import configparser
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)

# Load the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize the NetworkResolver
resolver = NetworkResolver(config)

# Resolve Redis host and Ollama API endpoint
redis_host = resolver.resolve_host()
ollama_endpoint = resolver.resolve_ollama_endpoint()

# Connect to Redis
redis_port = config['Redis'].getint('redis_port', 6379)
redis_manager = RedisManager(redis_host, redis_port)

# Initialize the InstitutionManager
institution_manager = InstitutionManager(redis_manager)

# Set up the snapshot manager
snapshot_manager = RedisSnapshotManager(redis_manager.redis_client)

# Set up LoginManager
login_manager = LoginManager()

# Streamlit UI
st.title("Admin Dashboard")

# Check if user is logged in by verifying session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def reset_session_state():
    """Reset session state variables."""
    st.session_state.pop('all_entries', None)
    st.session_state.pop('selected_entries', None)
    st.session_state.pop('total_entries', None)
    st.session_state.pop('current_index', None)

def reset_institution_data():
    """Reset data in Redis and reset session state variables."""
    selected_institution = st.session_state.get('institution_select', 'UAB')  # Default to 'UAB' if not set
    institution_manager.reset_institution_data(selected_institution)  # Reset data in Redis
    reset_session_state()

# If the user is not logged in, show the login form
if not st.session_state['logged_in']:
    st.markdown("## Admin Login")
    admin_username = st.text_input("Username")
    admin_password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_manager.login(st.session_state, admin_username, admin_password):
            st.session_state['logged_in'] = True  # Set the logged_in flag to True on successful login
            st.success("Login successful!")
            st.rerun()  # Refresh the page after login
        else:
            st.error("Invalid username or password")
else:
    # If the user is logged in, display the dashboard

    # Handle institution selection with a callback to reset the session state
    institution = st.selectbox(
        "Select Institution", ["UAB", "MBPCC"],
        key='institution_select',
        on_change=reset_session_state
    )

    # Pull all entries from Redis or refresh when institution is changed
    if 'all_entries' not in st.session_state or not st.session_state['all_entries']:
        all_entries, _ = institution_manager.get_institution_data(institution)
        st.session_state['all_entries'] = all_entries
        st.session_state['total_entries'] = len(all_entries)
    else:
        all_entries = st.session_state['all_entries']
        st.session_state['total_entries'] = len(all_entries)  # Ensure total_entries is updated

    # Get selected entries
    selected_entries = [entry for entry in st.session_state['all_entries'] if entry.get('Selected') == 'Select for Evaluation']

    # Total selected
    total_selected = len(selected_entries)
    total_entries = st.session_state.get('total_entries', 0)

    # Default mode to "Overview Mode"
    mode = st.radio("Choose Mode", ["Selection Mode", "Overview Mode"], index=0)

    # Display the appropriate page based on the selected mode
    if mode == "Selection Mode":
        selection_page = SelectionPage(institution_manager, institution)
        selection_page.show()
    elif mode == "Overview Mode":
        overview_page = OverviewPage(institution_manager, institution)
        overview_page.show()

        # Only display administrative options in Overview Mode
        # Redis Snapshot and Reload Functionality
        st.markdown("### Redis Snapshot and Data Management")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("Take Snapshot"):
                snapshot_manager.take_snapshot(institution)
                st.success(f"Snapshot for {institution} taken successfully!")
                st.rerun()

        with col2:
            if st.button("Reload Snapshot"):
                snapshot_manager.load_snapshot(institution)
                reset_session_state()  # Clear session state variables
                st.success(f"Reloaded {institution} data from snapshot!")
                st.rerun()

        with col3:
            if st.button("Reset Data"):
                reset_institution_data()
                st.success(f"All data for {institution} has been reset.")
                st.rerun()

        # Handle new data upload
        st.markdown("### Upload New Data")

        with st.form(key='upload_form'):
            uploaded_file = st.file_uploader("Upload New Data", type="xlsx")
            submit_upload = st.form_submit_button('Upload')

        if submit_upload:
            if uploaded_file is not None:
                try:
                    df = pd.read_excel(uploaded_file)
                    new_entries = df.to_dict(orient="records")
                    # Initialize entries with default values
                    institution_manager.initialize_entries(institution, new_entries)
                    reset_session_state()  # Clear session state variables
                    st.success(f"New data for {institution} uploaded successfully!")
                    st.rerun()  # Refresh the page to update counts
                except Exception as e:
                    st.error(f"Error processing uploaded file: {e}")
            else:
                st.warning("Please upload a file before clicking 'Upload'.")

    # Show total number of entries in the interface
    st.write(f"Total number of entries in database: {total_entries}")

    # Logout button
    if st.button("Logout"):
        login_manager.logout(st.session_state)
        st.session_state['logged_in'] = False  # Update the session state to indicate logout
        st.rerun()  # Refresh the page after logout
