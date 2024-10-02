# user_submission.py

import streamlit as st
import pandas as pd
import numpy as np
from login_manager import LoginManager
from institution_manager import InstitutionManager
from redis_manager import RedisManager
from network_resolver import NetworkResolver
import configparser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize the NetworkResolver
resolver = NetworkResolver(config)

# Resolve Redis host
redis_host = resolver.resolve_host()
redis_port = config['Redis'].getint('redis_port', 6379)
redis_manager = RedisManager(redis_host, redis_port)

# Initialize the InstitutionManager
institution_manager = InstitutionManager(redis_manager)

# Initialize the LoginManager
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
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
else:
    # Evaluator is logged in
    st.markdown(f"### Welcome, {st.session_state['evaluator_username']}!")

    # Select Institution
    institution = st.selectbox(
        "Select Institution", ["UAB", "MBPCC"],
        key='evaluator_institution_select',
    )

    # Load assigned entries
    if 'assigned_entries' not in st.session_state:
        # For simplicity, assign all selected entries to the evaluator
        all_entries, _ = institution_manager.get_institution_data(institution)
        assigned_entries = [
            entry for entry in all_entries if entry.get('Selected') == 'Select for Evaluation'
        ]
        st.session_state['assigned_entries'] = assigned_entries
        st.session_state['total_assigned_entries'] = len(assigned_entries)
    else:
        assigned_entries = st.session_state['assigned_entries']

    total_assigned_entries = st.session_state.get('total_assigned_entries', 0)

    if total_assigned_entries == 0:
        st.write("No entries assigned for evaluation.")
    else:
        # Initialize current evaluation index
        if 'current_eval_index' not in st.session_state:
            st.session_state['current_eval_index'] = 0

        # Ensure index is within bounds
        if st.session_state.current_eval_index >= total_assigned_entries:
            st.session_state.current_eval_index = total_assigned_entries - 1
        if st.session_state.current_eval_index < 0:
            st.session_state.current_eval_index = 0

        # Navigation
        st.markdown("### Navigate Entries")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("Previous Entry") and st.session_state.current_eval_index > 0:
                st.session_state.current_eval_index -= 1
        with col2:
            # Slider to navigate entries
            st.session_state.current_eval_index = st.slider(
                "Select Entry",
                min_value=0,
                max_value=total_assigned_entries - 1,
                value=st.session_state.current_eval_index,
                format="Entry %d",
                key='eval_entry_slider'
            )
        with col3:
            if st.button("Next Entry") and st.session_state.current_eval_index < total_assigned_entries - 1:
                st.session_state.current_eval_index += 1

        current_entry = assigned_entries[st.session_state.current_eval_index]

        # Display progress bar or visual indicator
        progress = (st.session_state.current_eval_index + 1) / total_assigned_entries
        st.progress(progress)

        # Display the current entry
        st.write(f"### Event Number: {current_entry.get('Event Number', 'N/A')}")

        st.markdown("#### Original Narrative")
        st.write(current_entry.get('Narrative', ''))

        st.markdown("#### Succinct Summary")
        st.write(current_entry.get('Succinct Summary', ''))
        summary_score = st.slider("Rate the Succinct Summary (1-5)", min_value=1, max_value=5, key='summary_score')

        st.markdown("#### Assigned Tags")
        st.write(current_entry.get('Assigned Tags', ''))
        tag_score = st.slider("Rate the Assigned Tags (1-5)", min_value=1, max_value=5, key='tag_score')

        st.markdown("#### Provide Your Feedback")
        feedback = st.text_area("Feedback", key='evaluation_feedback')

        if st.button("Submit Evaluation"):
            # Save evaluation
            evaluation = {
                'Evaluator': st.session_state['evaluator_username'],
                'Summary Score': summary_score,
                'Tag Score': tag_score,
                'Feedback': feedback
            }
            # Add evaluation to the entry
            if 'Evaluations' not in current_entry:
                current_entry['Evaluations'] = []
            current_entry['Evaluations'].append(evaluation)

            # Update entry in Redis
            institution_manager.update_entry(institution, current_entry)

            # Update session state
            st.session_state['assigned_entries'][st.session_state.current_eval_index] = current_entry

            st.success("Evaluation submitted successfully!")

        # Logout button
        if st.button("Logout"):
            st.session_state['evaluator_logged_in'] = False
            st.session_state.pop('assigned_entries', None)
            st.session_state.pop('current_eval_index', None)
            st.success("Logged out successfully!")
            st.experimental_rerun()
