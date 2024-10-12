# app.py

import streamlit as st
import configparser
import logging
import pandas as pd
from database_manager import DatabaseManager
from network_resolver import NetworkResolver
from login_manager import LoginManager
from selection_page import SelectionPage
from overview_page import OverviewPage
from analysis_page import AnalysisPage
from analysis_methods import evaluate_and_tag_entries  # Import evaluation methods

# Set up logging for debugging
logging.basicConfig(level=logging.WARNING)

# Load the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize the NetworkResolver
resolver = NetworkResolver(config)

# Resolve Redis host, PostgreSQL, and Ollama API endpoint
redis_host, ollama_endpoint = resolver.resolve_all()

# Resolve PostgreSQL credentials dynamically based on the network
local_ip = resolver.get_local_ip()
environment = resolver.resolve_environment(local_ip)

# Extract PostgreSQL and Redis configuration based on the environment
psql_host = config['postgresql'][f'psql_{environment}']
psql_port = config['postgresql'].getint('psql_port', 5432)
psql_user = config['postgresql']['psql_user']
psql_password = config['postgresql']['psql_password']
psql_dbname = config['postgresql']['psql_dbname']
redis_port = config['Redis'].getint('redis_port', 6379)

# Initialize the DatabaseManager with the resolved credentials
db_manager = DatabaseManager(
    redis_host=redis_host,
    redis_port=redis_port,
    psql_host=psql_host,
    psql_port=psql_port,
    psql_user=psql_user,
    psql_password=psql_password,
    psql_dbname=psql_dbname
)

# Initialize the LoginManager
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

# Updated reset function in app.py

def reset_institution_data():
    selected_institution = st.session_state.get('institution_select', 'UAB')  # Default to 'UAB' if not set
    try:
        st.write(f"Resetting data for institution: {selected_institution}")
        db_manager.reset_data(selected_institution)  # Reset data in both Redis and PostgreSQL
        
        # Ensure session state is cleared after resetting
        reset_session_state()
        st.success(f"All data for {selected_institution} has been reset.")
        
    except Exception as e:
        st.error(f"Error during reset: {e}")


# If the user is not logged in, show the login form
if not st.session_state['logged_in']:
    st.markdown("## Admin Login")
    admin_username = st.text_input("Username")
    admin_password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_manager.login(st.session_state, admin_username, admin_password):
            st.session_state['logged_in'] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")
else:
    # Check if the user has admin role
    if st.session_state.get('user_role') != 'admin':
        st.error("You do not have permission to access this page.")
        if st.button("Logout"):
            login_manager.logout(st.session_state)
            st.session_state['logged_in'] = False
            st.rerun()
    else:
        # If the user is logged in and has admin role, display the dashboard
        institution = st.selectbox("Select Institution", ["UAB", "MBPCC"], key='institution_select', on_change=reset_session_state)

        # Pull all entries from Redis or refresh when institution is changed
        if 'all_entries' not in st.session_state:
            all_entries = db_manager.get_selected_entries(institution)
            evaluation_scores = db_manager.get_evaluation_scores(institution)

            if not all_entries:
                st.session_state['all_entries'] = []
                st.session_state['evaluation_scores'] = {}
                st.session_state['total_entries'] = 0
                st.warning("No data available for the selected institution.")
            else:
                st.session_state['all_entries'] = all_entries
                st.session_state['evaluation_scores'] = evaluation_scores
                st.session_state['total_entries'] = len(all_entries)
        else:
            all_entries = st.session_state['all_entries']
            evaluation_scores = st.session_state['evaluation_scores']
            st.session_state['total_entries'] = len(all_entries)

        # Choose the mode and display pages
        mode = st.radio("Choose Mode", ["Selection Mode", "Overview Mode", "Analysis Mode"], index=0)

        if mode == "Analysis Mode" and st.session_state['total_entries'] > 0:
            # Perform analysis using analysis_methods.py
            analyzed_entries = evaluate_and_tag_entries(all_entries)
            # Process analysis and display the results
            analysis_page = AnalysisPage(db_manager)  # Pass only db_manager
            analysis_page.show()

        elif mode == "Selection Mode" and st.session_state['total_entries'] > 0:
            selection_page = SelectionPage(db_manager, institution)
            selection_page.show()
        elif mode == "Overview Mode":
            overview_page = OverviewPage(db_manager, institution)
            overview_page.show()

            # Admin options for snapshots, data reset, and uploads
            st.markdown("### Redis Snapshot and Data Management")
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.button("Take Snapshot"):
                    db_manager.take_snapshot(institution)
                    st.success(f"Snapshot for {institution} taken successfully!")
                    st.rerun()

            with col2:
                if st.button("Load Snapshot"):
                    db_manager.load_snapshot(institution)
                    reset_session_state()
                    st.success(f"Reloaded {institution} data from snapshot!")
                    st.rerun()

            with col3:
                # After Reset Data Button
                if st.button("Reset Data"):
                    reset_institution_data()
                    # Ensure session state is cleared after resetting
                    reset_session_state()
                    st.success(f"All data for {institution} has been reset.")
                    st.rerun()




            # Handle data upload
            st.markdown("### Upload New Data")
            with st.form(key='upload_form'):
                uploaded_file = st.file_uploader("Upload New Data", type="xlsx")
                submit_upload = st.form_submit_button('Upload')

                if submit_upload:
                    if uploaded_file is not None:
                        try:
                            # Read the uploaded file into a pandas DataFrame
                            df = pd.read_excel(uploaded_file)
                            # Convert the DataFrame to a list of dictionaries (entries)
                            new_entries = df.to_dict(orient="records")

                            # Ensure that 'Selected' is set to 'Do Not Select' by default
                            for entry in new_entries:
                                entry['Selected'] = 'Do Not Select'  # Force 'Do Not Select' for every entry

                            logging.info(f"Parsed {len(new_entries)} entries from the uploaded file.")

                            # Save entries to the database (both Redis and PostgreSQL)
                            db_manager.save_selected_entries(institution, new_entries)

                            # Force reload the entries into session state
                            all_entries = db_manager.get_selected_entries(institution)
                            st.session_state['all_entries'] = all_entries
                            st.session_state['total_entries'] = len(all_entries)

                            st.success(f"New data for {institution} uploaded successfully!")
                            st.experimental_rerun()  # Refresh the page so that the new data is displayed immediately
                        except Exception as e:
                            logging.error(f"Error processing uploaded file: {e}")
                            st.error(f"Error processing uploaded file: {e}")
                    else:
                        st.warning("Please upload a file before clicking 'Upload'.")



        st.write(f"Total number of entries in database: {st.session_state['total_entries']}")

        if st.button("Logout"):
            login_manager.logout(st.session_state)
            st.session_state['logged_in'] = False
            st.rerun()
