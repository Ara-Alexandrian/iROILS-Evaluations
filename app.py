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

# Determine the environment using the NetworkResolver
local_ip = resolver.get_local_ip()
environment = resolver.resolve_environment(local_ip)

# Extract PostgreSQL credentials based on the environment
psql_host = config['postgresql'][f'psql_{environment}']  # Use 'psql_home' or 'psql_work'
psql_port = config['postgresql'].getint('psql_port', 5432)
psql_user = config['postgresql']['psql_user']
psql_password = config['postgresql']['psql_password']
psql_dbname = config['postgresql']['psql_dbname']

# Initialize the DatabaseManager with the resolved credentials
db_manager = DatabaseManager(
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
    st.session_state.pop('total_entries', None)
    st.session_state.pop('current_index', None)

def reset_institution_data():
    selected_institution = st.session_state.get('institution_select', 'UAB')  # Default to 'UAB' if not set
    try:
        st.write(f"Resetting data for institution: {selected_institution}")
        db_manager.reset_data(selected_institution)  # Reset data in PostgreSQL

        # Ensure session state is cleared after resetting
        reset_session_state()
        st.success(f"All data for {selected_institution} has been reset.")

    except Exception as e:
        st.error(f"Error during reset: {e}")

def render_file_upload():
    """Handle the file upload process."""
    st.markdown("### Upload New Data")
    uploaded_file = st.file_uploader("Upload New Data", type="xlsx")

    if uploaded_file:
        try:
            # Read the uploaded file into a pandas DataFrame
            df = pd.read_excel(uploaded_file)

            # Replace NaN values with None (null in JSON)
            df = df.where(pd.notnull(df), None)

            # Remove 'Selected' column if it exists
            if 'Selected' in df.columns:
                df.drop(columns=['Selected'], inplace=True)
                st.write("Removed 'Selected' column from uploaded data.")

            # Convert the DataFrame to a list of dictionaries (entries)
            new_entries = df.to_dict(orient="records")

            # Ensure that 'Selected' is set to 'Do Not Select' by default
            for entry in new_entries:
                entry['Selected'] = 'Do Not Select'  # Force 'Do Not Select' for every entry

            logging.info(f"Parsed {len(new_entries)} entries from the uploaded file.")

            # Save entries to the database (PostgreSQL)
            db_manager.save_selected_entries(st.session_state['institution_select'], new_entries)

            # Force reload the entries into session state
            all_entries = db_manager.get_selected_entries(st.session_state['institution_select'])
            st.session_state['all_entries'] = all_entries
            st.session_state['total_entries'] = len(all_entries)

            st.success(f"New data for {st.session_state['institution_select']} uploaded successfully!")
            st.rerun()  # Refresh the page so that the new data is displayed immediately
        except Exception as e:
            logging.error(f"Error processing uploaded file: {e}")
            st.error(f"Error processing uploaded file: {e}")
    else:
        st.warning("Please upload a file before clicking 'Upload'.")

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

        # Pull all entries from PostgreSQL or refresh when institution is changed
        if 'all_entries' not in st.session_state:
            all_entries = db_manager.get_selected_entries(institution)

            if not all_entries:
                st.session_state['all_entries'] = []
                st.session_state['total_entries'] = 0
                st.warning("No data available for the selected institution.")
            else:
                st.session_state['all_entries'] = all_entries
                st.session_state['total_entries'] = len(all_entries)
        else:
            all_entries = st.session_state['all_entries']
            st.session_state['total_entries'] = len(all_entries)

        # Choose the mode and display pages
        mode = st.radio("Choose Mode", ["Selection Mode", "Overview Mode", "Analysis Mode"], index=0)

        if mode == "Analysis Mode" and st.session_state['total_entries'] > 0:
            # Perform analysis using analysis_methods.py
            analyzed_entries = evaluate_and_tag_entries(all_entries)
            # Process analysis and display the results
            analysis_page = AnalysisPage(db_manager)
            analysis_page.show()

        elif mode == "Selection Mode" and st.session_state['total_entries'] > 0:
            selection_page = SelectionPage(db_manager, institution)
            selection_page.show()

        elif mode == "Overview Mode":
            overview_page = OverviewPage(db_manager, institution)
            overview_page.show()

            # **Data Management Options**
            st.markdown("### Data Management")
            
            # Add the Upload Button
            render_file_upload()

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Reset Data"):
                    reset_institution_data()
                    st.rerun()

            if st.button("Logout"):
                login_manager.logout(st.session_state)
                st.session_state['logged_in'] = False
                st.rerun()

