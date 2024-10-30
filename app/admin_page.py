# app/app.py

import streamlit as st
import logging
import pandas as pd
from config.config_manager import ConfigManager
from utils.database_manager import DatabaseManager
from utils.network_resolver import NetworkResolver
from utils.login_manager import LoginManager
from pages.selection_page import SelectionPage
from pages.overview_page import OverviewPage
from pages.analysis_page import AnalysisPage

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize configuration
config_manager = ConfigManager()
resolver = NetworkResolver(config_manager)

# Determine environment and get configuration
local_ip = resolver.get_local_ip()
environment = resolver.resolve_environment(local_ip)
pg_config = config_manager.get_postgresql_config(environment)

# Initialize managers
db_manager = DatabaseManager(
  psql_host=pg_config['host'],
  psql_port=pg_config['port'],
  psql_user=pg_config['user'],
  psql_password=pg_config['password'],
  psql_dbname=pg_config['dbname']
)
login_manager = LoginManager()

# Streamlit UI
st.title("Admin Dashboard")

# Check if user is logged in by verifying session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Function to reset session state
def reset_session_state():
    st.session_state.pop('all_entries', None)
    st.session_state.pop('total_entries', None)
    st.session_state.pop('current_index', None)

# Function to reset institution data
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

# File upload handler
def render_file_upload():
    st.markdown("### Upload New Data")
    uploaded_file = st.file_uploader("Upload New Data", type="xlsx")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df = df.where(pd.notnull(df), None)

            if 'Selected' in df.columns:
                df.drop(columns=['Selected'], inplace=True)
                st.write("Removed 'Selected' column from uploaded data.")

            new_entries = df.to_dict(orient="records")
            for entry in new_entries:
                entry['Selected'] = 'Do Not Select'  # Force 'Do Not Select' for every entry

            logging.info(f"Parsed {len(new_entries)} entries from the uploaded file.")
            db_manager.save_selected_entries(st.session_state['institution_select'], new_entries)

            all_entries = db_manager.get_selected_entries(st.session_state['institution_select'])
            st.session_state['all_entries'] = all_entries
            st.session_state['total_entries'] = len(all_entries)

            st.success(f"New data for {st.session_state['institution_select']} uploaded successfully!")
            st.rerun()  # Refresh the page so the new data is displayed immediately
        except Exception as e:
            logging.error(f"Error processing uploaded file: {e}")
            st.error(f"Error processing uploaded file: {e}")
    else:
        st.warning("Please upload a file before clicking 'Upload'.")

# If the user is not logged in, show the login form
if not st.session_state['logged_in']:
    st.markdown("## Admin Login")

    # Wrap inputs inside a form to enable 'Enter' key submission
    with st.form(key="admin_login_form"):
        admin_username = st.text_input("Username")
        admin_password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button(label="Login")

    # Process form submission
    if submit_button:
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

        mode = st.radio("Choose Mode", ["Selection Mode", "Overview Mode", "Analysis Mode"], index=0)

        if mode == "Analysis Mode" and st.session_state['total_entries'] > 0:
            analyzed_entries = evaluate_and_tag_entries(all_entries)
            analysis_page = AnalysisPage(db_manager)
            analysis_page.show()

        elif mode == "Selection Mode" and st.session_state['total_entries'] > 0:
            selection_page = SelectionPage(db_manager, institution)
            selection_page.show()

        elif mode == "Overview Mode":
            overview_page = OverviewPage(db_manager, institution)
            overview_page.show()

            st.markdown("### Data Management")
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
