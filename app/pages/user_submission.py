import streamlit as st
import configparser
import logging
from database_manager import DatabaseManager
from login_manager import LoginManager

# Set up logging for debugging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Load the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize PostgreSQL credentials
environment = 'home'
psql_host = config['postgresql'][f'psql_{environment}']
psql_port = config['postgresql'].getint('psql_port', 5432)
psql_user = config['postgresql']['psql_user']
psql_password = config['postgresql']['psql_password']
psql_dbname = config['postgresql']['psql_dbname']

# Initialize DatabaseManager and LoginManager
db_manager = DatabaseManager(
    psql_host=psql_host,
    psql_port=psql_port,
    psql_user=psql_user,
    psql_password=psql_password,
    psql_dbname=psql_dbname
)
login_manager = LoginManager()

# Function to refresh data (clearing session state and reloading entries)
def refresh_data():
    st.session_state.pop('assigned_entries', None)
    st.session_state.pop('total_assigned_entries', None)
    st.session_state.pop('current_eval_index', None)
    st.session_state.pop('re_evaluating', None)
    st.rerun()

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
        
        if login_success:  # Assuming login_success is a boolean (True/False)
            st.success("Login successful!")
            evaluator_institution = "UAB"  # Replace with actual institution retrieval logic
            st.session_state['evaluator_username'] = evaluator_username
            st.session_state['evaluator_institution'] = evaluator_institution
            st.session_state['evaluator_logged_in'] = True
            st.session_state['current_eval_index'] = 0
            refresh_data()  # Automatically refresh data after login
        else:
            st.error("Invalid username or password")
else:
    # Evaluator is logged in
    evaluator_username = st.session_state['evaluator_username']
    evaluator_institution = st.session_state['evaluator_institution']

    # Global and institution-specific styles
    global_style = """
    <style>
        body, .stApp {
            background: linear-gradient(to bottom, #111111, #440000);
            color: #f2f2f2;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Segoe UI', sans-serif;
        }
        .stProgress > div > div > div > div {
            background-color: #ff6666;
        }
        .stTextArea, .stSlider, .stButton>button, .stRadio>div {
            box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
            border-radius: 5px;
            margin: 10px 0px;
        }
        .stButton>button:hover {
            background-color: #ff4d4d;
        }
        .stMarkdown, .stTextArea, .stSlider {
            padding: 10px;
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.1);
        }
        h1 {
            text-align: center;
            margin-top: 10px;
        }
    </style>
    """
    uab_style = """
    <style>
        body, .stApp {
            background: linear-gradient(to bottom, #0d1b0e, #003300);
            color: #e6e6e6;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #ffcc00;
        }
        .stButton>button {
            background-color: #ffcc00;
            color: #003300;
        }
        .stProgress > div > div > div > div {
            background-color: #ffcc00;
        }
    </style>
    """
    mbpcc_style = """
    <style>
        body, .stApp {
            background: linear-gradient(to bottom, #1a1a1a, #800000);
            color: #f2f2f2;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #ff4d4d;
        }
        .stButton>button {
            background-color: #ff1a1a;
            color: #000000;
        }
        .stProgress > div > div > div > div {
            background-color: #ff4d4d;
        }
    </style>
    """

    # Apply the global and institution-specific styling
    st.markdown(global_style, unsafe_allow_html=True)
    if evaluator_institution.lower() == 'uab':
        st.markdown(uab_style, unsafe_allow_html=True)
    elif evaluator_institution.lower() == 'mbpcc':
        st.markdown(mbpcc_style, unsafe_allow_html=True)

    # Logo and title
    logo_path = f"resources/{evaluator_institution.upper()}.png"
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo_path, width=200)
    st.title("Evaluator Dashboard")

    # Refresh Data Button
    if st.button("Refresh Data"):
        refresh_data()

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
            st.rerun()  # **Trigger rerun only once**

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
            if current_eval_index >= total_assigned_entries:
                current_eval_index = total_assigned_entries - 1
            if current_eval_index < 0:
                current_eval_index = 0

            st.session_state['current_eval_index'] = current_eval_index
            current_entry = assigned_entries[current_eval_index]

            # Navigation tools
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("Previous Entry") and current_eval_index > 0:
                    st.session_state['current_eval_index'] -= 1
                    st.rerun()
            with col3:
                if st.button("Next Entry") and current_eval_index < total_assigned_entries - 1:
                    st.session_state['current_eval_index'] += 1
                    st.rerun()

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
                    st.rerun()
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
                        
                        # Force page rerun to refresh the data
                        st.rerun()

                    except Exception as e:
                        logger.error(f"Error saving evaluation: {e}")
                        st.error("An error occurred while saving your evaluation. Please try again.")


    # Progress & Statistics Page
    elif page_selection == "Progress & Statistics":
        st.markdown(f"### Progress for {evaluator_username}")

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
        st.rerun()

    # Logout Button
    if st.button("Logout"):
        login_manager.logout(st.session_state)
        st.session_state['evaluator_logged_in'] = False
        st.rerun()
