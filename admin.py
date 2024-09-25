import streamlit as st
import pandas as pd
from redis_manager import RedisManager, RedisSnapshotManager
from login_manager import LoginManager
from institution_manager import InstitutionManager
from network_resolver import NetworkResolver
from selection_page import SelectionPage  # Make sure this path is correct
from overview_page import OverviewPage    # Make sure this path is correct
import configparser
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)

# Load the .ini configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize the NetworkResolver and resolve the Redis host
resolver = NetworkResolver(config)
redis_host = resolver.resolve_host()

# Connect to Redis
redis_port = config['Redis'].get('redis_port', 6379)
redis_manager = RedisManager(redis_host, redis_port)

# Set up the snapshot manager
snapshot_manager = RedisSnapshotManager(redis_manager.redis_client)

# Initialize the InstitutionManager
institution_manager = InstitutionManager(redis_manager)

# Set up LoginManager
login_manager = LoginManager()

# Streamlit UI
st.title("Admin Dashboard")

# Check if user is logged in by verifying session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# If the user is logged in, display the dashboard
if st.session_state['logged_in']:
    institution = st.selectbox("Select Institution", ["UAB", "MBPCC"])

    # Get the total number of entries for the institution
    selected_entries, evaluation_scores = institution_manager.get_institution_data(institution)

    # ** Placeholder: Set evaluation_scores to empty if no evaluations exist yet
    if not evaluation_scores:
        evaluation_scores = {"Placeholder": "No evaluations yet"}  # Placeholder entry

    total_entries = len(selected_entries)

    # Pull the selected entries from Redis (initialize if not done)
    if 'selected_entries' not in st.session_state:
        selected_entries = institution_manager.get_selected_entries(institution)
        st.session_state['selected_entries'] = selected_entries
    else:
        selected_entries = st.session_state['selected_entries']

    # Total selected
    total_selected = len(selected_entries)

    # Default mode to "Overview Mode"
    mode = st.radio("Choose Mode", ["Selection Mode", "Overview Mode"], index=1)

    # Display the appropriate page based on the selected mode
    if mode == "Selection Mode":
        selection_page = SelectionPage(institution_manager, institution)
        selection_page.show()
    elif mode == "Overview Mode":
        overview_page = OverviewPage(institution_manager, institution)
        overview_page.show(evaluation_scores)  # Passing evaluation scores to the overview page

    # Show total selected/total entries in the interface
    st.write(f"Total Selected Entries: {total_selected} / {total_entries}")

    # Redis Snapshot and Reload Functionality
    st.markdown("### Redis Snapshot and Data Management")

    if st.button(f"Take Snapshot for {institution}"):
        snapshot_manager.take_snapshot(institution)
        st.success(f"Snapshot for {institution} taken successfully!")

    if st.button(f"Reload {institution} Data from Snapshot"):
        snapshot_manager.load_snapshot(institution)
        st.success(f"Reloaded {institution} data from snapshot!")

    # **New Reset Button**: Reset Redis data for this institution
    if st.button(f"Reset {institution} Data"):
        institution_manager.reset_institution_data(institution)
        st.session_state['selected_entries'] = []  # Clear selected entries from session state
        st.success(f"All data for {institution} has been reset.")

    # Handle new data upload
    uploaded_file = st.file_uploader("Upload New Data", type="xlsx")
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        new_selected_entries = df.to_dict(orient="records")
        institution_manager.save_institution_data(institution, new_selected_entries, evaluation_scores)
        st.success(f"New data for {institution} uploaded successfully!")

    # Logout button
    if st.button("Logout"):
        login_manager.logout(st.session_state)
        st.session_state['logged_in'] = False  # Update the session state to indicate logout
        st.rerun()  # Refresh the page after logout

# If the user is not logged in, show the login form
else:
    admin_username = st.text_input("Username")
    admin_password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_manager.login(st.session_state, admin_username, admin_password):
            st.session_state['logged_in'] = True  # Set the logged_in flag to True on successful login
            st.success("Login successful!")
            st.rerun()  # Refresh the page after login
        else:
            st.error("Invalid username or password")
