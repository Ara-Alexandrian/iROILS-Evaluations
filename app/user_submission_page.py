import os
import streamlit as st
import logging
import time
from config.config_manager import ConfigManager
from utils.database_manager import DatabaseManager
from utils.network_resolver import NetworkResolver
from utils.login_manager import LoginManager

# Function to load and display logo based on institution
def load_logo(evaluator_institution):
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'resources', f'{evaluator_institution.upper()}.png')

    # Check if the logo file exists and display it
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        st.error(f"Logo for {evaluator_institution.upper()} not found.")

# Function to apply institution-specific styles
def apply_institution_style(evaluator_institution):
    if evaluator_institution.lower() == 'uab':
        style = """
        <style>
            body, .stApp {
                background: linear-gradient(to top, #0d1b0e, #003300);
                color: #e6e6e6;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #ffcc00;
            }
            .stButton>button {
                background-color: #ffcc00;
                color: #003300;
                border: 2px solid #e6e6e6;
                border-radius: 10px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
                font-weight: bold;
                padding: 0.6em 1.2em;
                transition: background-color 0.3s ease, box-shadow 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #ffe066;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.7);
            }
            .stSlider > div > div > div > div {
                background-color: #ffcc00;
                border-radius: 10px;
            }
            .stTextArea>textarea {
                background-color: #2b2b2b;
                color: #e6e6e6;
                border: 1px solid #ffcc00;
                border-radius: 6px;
                padding: 0.8em;
            }
            p {
                font-family: 'Segoe UI', sans-serif;
                font-size: 1.1em;
                color: #e6e6e6;
                line-height: 1.6;
            }
        </style>
        """
    elif evaluator_institution.lower() == 'mbpcc':
        style = """
        <style>
            body, .stApp {
                background: linear-gradient(to top, #330000, #660000);
                color: #f2f2f2;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #ff4d4d;
                font-weight: bold;
            }
            .stButton>button {
                background-color: #cc3b3b;
                color: #ffffff;
                border: 1px solid #b32828;
                border-radius: 10px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
                font-weight: bold;
                padding: 0.6em 1.2em;
                transition: background-color 0.3s ease, box-shadow 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #e64a4a;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.7);
            }
            .stSlider > div > div > div > div {
                background-color: #ff6666;
                border-radius: 10px;
            }
            .stTextArea>textarea {
                background-color: #2b2b2b;
                color: #f2f2f2;
                border: 1px solid #ff4d4d;
                border-radius: 6px;
                padding: 0.8em;
            }
            p {
                font-family: 'Segoe UI', sans-serif;
                font-size: 1.1em;
                color: #e6e6e6;
                line-height: 1.6;
            }
        </style>
        """
    else:
        style = """
        <style>
            body, .stApp {
                background: linear-gradient(to top, #111111, #440000);
                color: #f2f2f2;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #ff6666;
                font-weight: bold;
            }
            .stButton>button {
                background-color: #ff6666;
                color: #ffffff;
                border: 2px solid #b32828;
                border-radius: 10px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
                font-weight: bold;
                padding: 0.6em 1.2em;
                transition: background-color 0.3s ease, box-shadow 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #ff9999;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.7);
            }
            .stSlider > div > div > div > div {
                background-color: #ff6666;
                border-radius: 10px;
            }
            .stTextArea>textarea {
                background-color: #2b2b2b;
                color: #f2f2f2;
                border: 1px solid #ff6666;
                border-radius: 6px;
                padding: 0.8em;
            }
            p {
                font-family: 'Segoe UI', sans-serif;
                font-size: 1.1em;
                color: #e6e6e6;
                line-height: 1.6;
            }
        </style>
        """
    st.markdown(style, unsafe_allow_html=True)

# Set up logging for debugging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize configuration
config_manager = ConfigManager()

# Determine environment and get configuration
resolver = NetworkResolver(config_manager)
local_ip = resolver.get_local_ip()
environment = resolver.resolve_environment(local_ip)
pg_config = config_manager.get_postgresql_config(environment)

# Initialize DatabaseManager and LoginManager
db_manager = DatabaseManager(
    psql_host=pg_config['host'],
    psql_port=pg_config['port'],
    psql_user=pg_config['user'],
    psql_password=pg_config['password'],
    psql_dbname=pg_config['dbname']
)
login_manager = LoginManager()

# Function to refresh data (clearing session state and reloading entries)
def refresh_data():
    st.session_state.pop('assigned_entries', None)
    st.session_state.pop('total_assigned_entries', None)
    st.session_state.pop('current_eval_index', None)
    st.session_state.pop('re_evaluating', None)

# Ensure rerun is called only after an action
rerun_needed = False

# Check if evaluator is logged in
if not st.session_state.get('evaluator_logged_in', False):
    st.markdown("## Evaluator Login")

    # Wrap the input fields in a form to enable "Enter" key submission
    with st.form(key='login_form'):
        evaluator_username = st.text_input("Username")
        evaluator_password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button(label="Login")

    # Process form submission
    if submit_button:
        login_success = login_manager.evaluator_login(st.session_state, evaluator_username, evaluator_password)

        if login_success:
            st.success("Login successful!")
            evaluator_institution = st.session_state['evaluator_institution']
            st.session_state['evaluator_username'] = evaluator_username
            st.session_state['evaluator_logged_in'] = True
            st.session_state['current_eval_index'] = 0
            rerun_needed = True
        else:
            st.error("Invalid username or password")

# Evaluate only if user is logged in
if st.session_state.get('evaluator_logged_in', False):
    evaluator_username = st.session_state['evaluator_username']
    evaluator_institution = st.session_state['evaluator_institution']

    # Apply institution-specific styles
    apply_institution_style(evaluator_institution)

    # Display logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        load_logo(evaluator_institution)

    st.title("Evaluator Dashboard")

    # Refresh Data Button
    if st.button("Refresh Data"):
        refresh_data()
        rerun_needed = True

    # Page navigation
    page_selection = st.radio("Choose Page", ["Evaluation Submission", "Progress & Statistics"])

    if page_selection == "Evaluation Submission":
        st.markdown(f"### Welcome, {evaluator_username}!")

        # Only refresh assigned entries once when the user first enters the page
        if 'assigned_entries' not in st.session_state:
            assigned_entries = db_manager.get_selected_entries(evaluator_institution)
            assigned_entries = [entry for entry in assigned_entries if entry.get('Selected') == 'Select for Evaluation']
            st.session_state['assigned_entries'] = assigned_entries
            st.session_state['total_assigned_entries'] = len(assigned_entries)
            st.session_state['first_unrated'] = True
            rerun_needed = True

        # Load assigned entries from session state after refreshing
        assigned_entries = st.session_state.get('assigned_entries', [])
        total_assigned_entries = len(assigned_entries)
        st.session_state['total_assigned_entries'] = total_assigned_entries

        if total_assigned_entries == 0:
            st.write("No entries assigned for evaluation.")
        else:
            # Navigate to first un-evaluated entry upon login
            if 'first_unrated' not in st.session_state:
                for i, entry in enumerate(assigned_entries):
                    event_number = entry.get('Event Number', '')
                    if not db_manager.get_evaluation(evaluator_username, event_number, evaluator_institution):
                        st.session_state['current_eval_index'] = i
                        break
                st.session_state['first_unrated'] = True

            # Ensure index is within bounds
            current_eval_index = st.session_state.get('current_eval_index', 0)
            current_eval_index = min(max(0, current_eval_index), total_assigned_entries - 1)
            st.session_state['current_eval_index'] = current_eval_index
            current_entry = assigned_entries[current_eval_index]

            # Navigation tools
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("Previous Entry") and current_eval_index > 0:
                    st.session_state['current_eval_index'] -= 1
                    rerun_needed = True
            with col3:
                if st.button("Next Entry") and current_eval_index < total_assigned_entries - 1:
                    st.session_state['current_eval_index'] += 1
                    rerun_needed = True

            # Display progress bar
            st.progress((current_eval_index + 1) / total_assigned_entries)

            # Display the current entry for evaluation
            st.write(f"### Entry {current_eval_index + 1} of {total_assigned_entries} - Event Number: {current_entry.get('Event Number', 'N/A')}")
            st.markdown("#### Original Narrative")
            st.write(current_entry.get('Narrative', ''))

            st.markdown("#### Succinct Summary")
            st.write(current_entry.get('Succinct Summary', ''))

            # Check if the evaluator has already evaluated this entry
            evaluator_previous_evaluation = db_manager.get_evaluation(
                evaluator_username,
                current_entry.get('Event Number', ''),
                evaluator_institution
            )

            # Use unique keys for each component to avoid conflicts
            summary_score_key = f"summary_score_{current_eval_index}"
            tag_score_key = f"tag_score_{current_eval_index}"
            feedback_key = f"evaluation_feedback_{current_eval_index}"

            st.markdown("#### Assigned Tags")
            st.write(current_entry.get('Assigned Tags', ''))

            # If evaluated, show scores and allow re-evaluation
            if evaluator_previous_evaluation and not st.session_state.get('re_evaluating', False):
                st.session_state['re_evaluating'] = False
                st.markdown("### This entry has already been evaluated by you.")
                st.write(f"**Summary Score:** {evaluator_previous_evaluation['summary_score']}")
                st.write(f"**Tag Score:** {evaluator_previous_evaluation['tag_score']}")
                st.write(f"**Feedback:** {evaluator_previous_evaluation['feedback']}")

                if st.button("Edit Evaluation"):
                    st.session_state['re_evaluating'] = True
                    rerun_needed = True
            else:
                # Only show submit button when not previously evaluated or in re-evaluation mode
                summary_score = st.session_state.get(summary_score_key, 3)
                tag_score = st.session_state.get(tag_score_key, 3)
                feedback = st.session_state.get(feedback_key, '')

                # Display sliders for input
                summary_score = st.slider("Rate the Succinct Summary (1-5)", min_value=1, max_value=5, value=summary_score, key=summary_score_key)
                tag_score = st.slider("Rate the Assigned Tags (1-5)", min_value=1, max_value=5, value=tag_score, key=tag_score_key)
                feedback = st.text_area("Feedback", value=feedback, key=feedback_key)

                # Submit button
                if st.button("Submit Evaluation"):
                    try:
                        db_manager.save_evaluation(
                            evaluator_username,
                            current_entry.get('Event Number', ''),
                            evaluator_institution,
                            summary_score,
                            tag_score,
                            feedback
                        )

                        st.success("Your evaluation has been submitted.")

                        # Clear session state related to the current entry
                        st.session_state.pop(f"summary_score_{current_eval_index}", None)
                        st.session_state.pop(f"tag_score_{current_eval_index}", None)
                        st.session_state.pop(f"evaluation_feedback_{current_eval_index}", None)

                        # Automatically move to the next entry
                        if st.session_state.get('current_eval_index', 0) < st.session_state['total_assigned_entries'] - 1:
                            st.session_state['current_eval_index'] += 1
                        else:
                            st.success("You have completed all assigned evaluations.")

                        rerun_needed = True

                    except Exception as e:
                        logger.error(f"Error saving evaluation: {e}")
                        st.error("An error occurred while saving your evaluation. Please try again.")

    # Progress & Statistics Page
    elif page_selection == "Progress & Statistics":
        st.markdown(f"### Progress for {evaluator_username}")

        if 'assigned_entries' not in st.session_state:
            assigned_entries = db_manager.get_selected_entries(evaluator_institution)
            st.session_state['assigned_entries'] = [entry for entry in assigned_entries if entry.get('Selected') == 'Select for Evaluation']

        # Count completed evaluations
        completed_evaluations = db_manager.count_evaluations_by_evaluator(evaluator_username, evaluator_institution)
        total_assigned_entries = len(st.session_state['assigned_entries'])
        completion_percentage = (completed_evaluations / total_assigned_entries) * 100 if total_assigned_entries > 0 else 0

        st.write(f"Entries Assigned: {total_assigned_entries}")
        st.write(f"Evaluations Completed: {completed_evaluations} ({completion_percentage:.2f}%)")
        st.progress(completion_percentage / 100)

        st.markdown("### Jump to an Entry")
        entry_selection = st.selectbox(
            "Select an Entry to Jump To",
            [f"Entry {i+1} - {entry.get('Event Number', 'N/A')} {'✅' if db_manager.get_evaluation(evaluator_username, entry.get('Event Number', ''), evaluator_institution) else '❌'}"
             for i, entry in enumerate(st.session_state['assigned_entries'])],
            index=st.session_state.get('current_eval_index', 0)
        )

        # Extract selected entry index
        selected_entry_index = int(entry_selection.split()[1]) - 1
        st.session_state['current_eval_index'] = selected_entry_index
        rerun_needed = True

    # Logout Button
    if st.button("Logout"):
        # Clear session state variables
        login_manager.logout(st.session_state)
        st.session_state['evaluator_logged_in'] = False
        st.session_state['evaluator_username'] = None
        st.session_state['evaluator_institution'] = None
        st.session_state['current_eval_index'] = None
        st.session_state.clear()  # Optionally clear all session state data
        
        # Instead of rerunning immediately, show a success message to confirm logout
        st.success("You have been logged out. Please log in again.")
        time.sleep(2)
        # Optionally, you can redirect back to login after a short delay
        st.rerun()

