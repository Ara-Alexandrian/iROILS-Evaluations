# user_submission.py

import streamlit as st
import pandas as pd
import numpy as np
from database_manager import DatabaseManager  # Now using DatabaseManager
from login_manager import LoginManager
from institution_manager import InstitutionManager
from network_resolver import NetworkResolver
import configparser
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize the NetworkResolver
resolver = NetworkResolver(config)

# Resolve Redis host, PostgreSQL, and Ollama API endpoint
redis_host, ollama_endpoint = resolver.resolve_all()

# Resolve PostgreSQL credentials dynamically based on the network
local_ip = resolver.get_local_ip()
environment = resolver.resolve_environment(local_ip)

# Extract PostgreSQL configuration based on the environment
psql_host = config['postgresql'][f'psql_{environment}']
psql_port = config['postgresql'].getint('psql_port', 5432)
psql_user = config['postgresql']['psql_user']
psql_password = config['postgresql']['psql_password']
psql_dbname = config['postgresql']['psql_dbname']
redis_port = config['Redis'].getint('redis_port', 6379)

# Initialize DatabaseManager with required credentials
db_manager = DatabaseManager(
    redis_host=redis_host,
    redis_port=redis_port,
    psql_host=psql_host,
    psql_port=psql_port,
    psql_user=psql_user,
    psql_password=psql_password,
    psql_dbname=psql_dbname
)

# Initialize the InstitutionManager with DatabaseManager
institution_manager = InstitutionManager(db_manager, db_manager)  # db_manager handles both Redis and PostgreSQL

# Initialize LoginManager
login_manager = LoginManager()

# Streamlit UI
st.title("Evaluator Dashboard")

# Check if evaluator is logged in
if not st.session_state.get('evaluator_logged_in', False):
    st.markdown("## Evaluator Login")
    evaluator_username = st.text_input("Username")
    evaluator_password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_manager.evaluator_login(st.session_state, evaluator_username, evaluator_password):
            st.success("Login successful!")
            # Load the last completed entry index from Redis for this evaluator
            last_completed_entry_index = db_manager.redis_client.get(f"{evaluator_username}:last_completed_entry_index")
            if last_completed_entry_index is not None:
                st.session_state['current_eval_index'] = int(last_completed_entry_index)
            else:
                st.session_state['current_eval_index'] = 0
            st.rerun()
        else:
            st.error("Invalid username or password")
else:
    # Evaluator is logged in
    evaluator_username = st.session_state['evaluator_username']
    evaluator_institution = st.session_state['evaluator_institution']

    # Add a Refresh Data button
    if st.button("Refresh Data"):
        st.session_state.pop('assigned_entries', None)
        st.session_state.pop('total_assigned_entries', None)
        st.session_state.pop('current_eval_index', None)
        st.session_state.pop('re_evaluating', None)
        st.rerun()

    # Page navigation
    page_selection = st.radio("Choose Page", ["Evaluation Submission", "Progress & Statistics"])

    if page_selection == "Evaluation Submission":
        st.markdown(f"### Welcome, {evaluator_username}!")

        # Load assigned entries only if not already in session state
        if 'assigned_entries' not in st.session_state:
            assigned_entries = db_manager.get_selected_entries(evaluator_institution)
            # Filter entries that are selected for evaluation
            assigned_entries = [
                entry for entry in assigned_entries if entry.get('Selected') == 'Select for Evaluation'
            ]
            st.session_state['assigned_entries'] = assigned_entries
            st.session_state['total_assigned_entries'] = len(assigned_entries)

        assigned_entries = st.session_state.get('assigned_entries', [])
        total_assigned_entries = st.session_state.get('total_assigned_entries', 0)

        if total_assigned_entries == 0:
            st.write("No entries assigned for evaluation.")
        else:
            # Ensure index is within bounds
            current_eval_index = st.session_state.get('current_eval_index', 0)
            if current_eval_index >= total_assigned_entries:
                current_eval_index = total_assigned_entries - 1
            if current_eval_index < 0:
                current_eval_index = 0

            current_entry = assigned_entries[current_eval_index]

            # Navigation tools
            st.markdown("### Navigate Entries")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("Previous Entry") and current_eval_index > 0:
                    st.session_state['current_eval_index'] -= 1
                    st.rerun()
            with col3:
                if st.button("Next Entry") and current_eval_index < total_assigned_entries - 1:
                    st.session_state['current_eval_index'] += 1
                    st.rerun()

            with col2:
                # Slider to navigate entries (enumerated from 1)
                st.session_state['current_eval_index'] = st.slider(
                    "Select Entry",
                    min_value=1,
                    max_value=total_assigned_entries,
                    value=current_eval_index + 1,
                    format="Entry %d",
                    key='eval_entry_slider'
                ) - 1  # Adjust index to be 0-based
                current_eval_index = st.session_state['current_eval_index']

            # Display progress bar
            progress = (current_eval_index + 1) / total_assigned_entries
            st.progress(progress)

            # Display the current entry for evaluation
            st.write(f"### Entry {current_eval_index + 1} of {total_assigned_entries} - Event Number: {current_entry.get('Event Number', 'N/A')}")
            st.markdown("#### Original Narrative")
            st.write(current_entry.get('Narrative', ''))

            st.markdown("#### Succinct Summary")
            st.write(current_entry.get('Succinct Summary', ''))

            # Check if the evaluator has already evaluated this entry
            evaluator_previous_evaluation = None
            for eval in current_entry.get('Evaluations', []):
                if eval['Evaluator'] == evaluator_username:
                    evaluator_previous_evaluation = eval
                    break

            if evaluator_previous_evaluation and not st.session_state.get('re_evaluating', False):
                st.markdown("### This entry has already been evaluated by you.")
                st.write(f"**Summary Score:** {evaluator_previous_evaluation['Summary Score']}")
                st.write(f"**Tag Score:** {evaluator_previous_evaluation['Tag Score']}")
                st.write(f"**Feedback:** {evaluator_previous_evaluation['Feedback']}")

                if st.button("Re-Evaluate Entry"):
                    st.session_state['re_evaluating'] = True
                    # Clear any existing session variables for this entry
                    st.session_state.pop(f"summary_score_{current_eval_index}", None)
                    st.session_state.pop(f"tag_score_{current_eval_index}", None)
                    st.session_state.pop(f"evaluation_feedback_{current_eval_index}", None)
                    st.rerun()
            else:
                # Set default values in session state when the entry changes or re-evaluating
                if f"summary_score_{current_eval_index}" not in st.session_state:
                    # If re-evaluating, pre-fill with previous values
                    if evaluator_previous_evaluation:
                        st.session_state[f"summary_score_{current_eval_index}"] = evaluator_previous_evaluation['Summary Score']
                    else:
                        st.session_state[f"summary_score_{current_eval_index}"] = 3  # Default value

                if f"tag_score_{current_eval_index}" not in st.session_state:
                    if evaluator_previous_evaluation:
                        st.session_state[f"tag_score_{current_eval_index}"] = evaluator_previous_evaluation['Tag Score']
                    else:
                        st.session_state[f"tag_score_{current_eval_index}"] = 3

                if f"evaluation_feedback_{current_eval_index}" not in st.session_state:
                    if evaluator_previous_evaluation:
                        st.session_state[f"evaluation_feedback_{current_eval_index}"] = evaluator_previous_evaluation['Feedback']
                    else:
                        st.session_state[f"evaluation_feedback_{current_eval_index}"] = ''

                # Use unique keys for each evaluation to avoid conflicts
                summary_score = st.slider("Rate the Succinct Summary (1-5)", min_value=1, max_value=5,
                                          key=f'summary_score_{current_eval_index}')

                st.markdown("#### Assigned Tags")
                st.write(current_entry.get('Assigned Tags', ''))

                tag_score = st.slider("Rate the Assigned Tags (1-5)", min_value=1, max_value=5,
                                      key=f'tag_score_{current_eval_index}')

                st.markdown("#### Provide Your Feedback")

                feedback = st.text_area("Feedback", key=f'evaluation_feedback_{current_eval_index}')

                if st.button("Submit Evaluation"):
                    # Save evaluation
                    evaluation = {
                        'Evaluator': evaluator_username,
                        'Summary Score': summary_score,
                        'Tag Score': tag_score,
                        'Feedback': feedback
                    }

                    # Update evaluations
                    existing_evaluations = current_entry.get('Evaluations', [])
                    if evaluator_previous_evaluation:
                        # Remove the old evaluation
                        existing_evaluations = [eval for eval in existing_evaluations if eval['Evaluator'] != evaluator_username]
                        is_new_evaluation = False
                        old_summary_score = evaluator_previous_evaluation['Summary Score']
                        old_tag_score = evaluator_previous_evaluation['Tag Score']
                    else:
                        is_new_evaluation = True
                        old_summary_score = 0
                        old_tag_score = 0

                    # Add the new evaluation
                    existing_evaluations.append(evaluation)
                    current_entry['Evaluations'] = existing_evaluations

                    # Update entry in the database
                    db_manager.update_entry(evaluator_institution, current_entry)

                    # Update institution statistics
                    db_manager.update_institution_stats(
                        evaluator_institution,
                        summary_score,
                        tag_score,
                        is_new_evaluation,
                        old_summary_score,
                        old_tag_score
                    )

                    # Save last completed entry index for this evaluator
                    db_manager.redis_client.set(f"{evaluator_username}:last_completed_entry_index", current_eval_index)

                    # Indicate success before moving to the next entry
                    st.markdown("### Submission Successful!")
                    st.success("Your evaluation has been submitted.")
                    # Reset 're_evaluating' state and clear session variables
                    st.session_state['re_evaluating'] = False
                    st.session_state.pop(f"summary_score_{current_eval_index}", None)
                    st.session_state.pop(f"tag_score_{current_eval_index}", None)
                    st.session_state.pop(f"evaluation_feedback_{current_eval_index}", None)
                    # Move to the next entry
                    if current_eval_index < total_assigned_entries - 1:
                        st.session_state['current_eval_index'] += 1
                    st.rerun()

    elif page_selection == "Progress & Statistics":
        st.markdown(f"### Progress for {evaluator_username}")

        # Calculate progress
        assigned_entries = st.session_state.get('assigned_entries', [])
        completed_evaluations = sum(
            1 for entry in assigned_entries if any(eval['Evaluator'] == evaluator_username for eval in entry.get('Evaluations', []))
        )
        st.write(f"Entries Assigned: {len(assigned_entries)}")
        st.write(f"Evaluations Completed: {completed_evaluations}")
        st.progress(completed_evaluations / len(assigned_entries) if assigned_entries else 0)

        # Display institution-specific statistics
        st.markdown(f"### {evaluator_institution} Statistics")

        # Retrieve statistics from the database
        stats = db_manager.get_institution_stats(evaluator_institution)

        if stats['total_evaluations'] > 0:
            cumulative_summary = stats['cumulative_summary']
            cumulative_tag = stats['cumulative_tag']
            total_evaluations = stats['total_evaluations']

            avg_summary = cumulative_summary / total_evaluations if total_evaluations > 0 else 0.0
            avg_tag = cumulative_tag / total_evaluations if total_evaluations > 0 else 0.0

            st.write(f"Total Evaluations: {total_evaluations}")
            st.metric("Average Summary Score", f"{avg_summary:.2f}")
            st.metric("Average Tag Score", f"{avg_tag:.2f}")
        else:
            st.write("No evaluations found for this institution.")

    # Logout button
    if st.button("Logout"):
        login_manager.logout(st.session_state)
        st.session_state['evaluator_logged_in'] = False
        st.rerun()
