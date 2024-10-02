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
            st.rerun()
        else:
            st.error("Invalid username or password")
else:
    # Evaluator is logged in
    st.markdown(f"### Welcome, {st.session_state['evaluator_username']}!")

    # Select Institution
    def on_institution_change():
        st.session_state.pop('assigned_entries', None)
        st.session_state.pop('current_eval_index', None)
        st.session_state.pop('total_assigned_entries', None)

    institution = st.selectbox(
        "Select Institution", ["UAB", "MBPCC"],
        key='evaluator_institution_select',
        on_change=on_institution_change
    )

    # Load assigned entries
    if 'assigned_entries' not in st.session_state:
        # Retrieve only the entries
        all_entries = institution_manager.get_all_entries(institution)
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
            st.session_state.current_eval_index = st.slider(
                "Select Entry",
                min_value=1,
                max_value=total_assigned_entries,
                value=st.session_state.current_eval_index + 1,
                format="Entry %d",
                key='eval_entry_slider'
            ) - 1
        with col3:
            if st.button("Next Entry") and st.session_state.current_eval_index < total_assigned_entries - 1:
                st.session_state.current_eval_index += 1

        current_entry = assigned_entries[st.session_state.current_eval_index]

        # Display progress bar
        progress = (st.session_state.current_eval_index + 1) / total_assigned_entries
        st.progress(progress)

        # Display the current entry
        st.write(f"### Entry {st.session_state.current_eval_index + 1} of {total_assigned_entries} - Event Number: {current_entry.get('Event Number', 'N/A')}")

        st.markdown("#### Original Narrative")
        st.write(current_entry.get('Narrative', ''))

        st.markdown("#### Succinct Summary")
        st.write(current_entry.get('Succinct Summary', ''))

        # Check if the evaluator has already evaluated this entry
        already_evaluated = any(
            eval['Evaluator'] == st.session_state['evaluator_username'] 
            for eval in current_entry.get('Evaluations', [])
        )

        if already_evaluated:
            st.markdown("### This entry has already been evaluated by you.")
        else:
            if f"summary_score_{st.session_state.current_eval_index}" not in st.session_state:
                st.session_state[f"summary_score_{st.session_state.current_eval_index}"] = 3

            if f"tag_score_{st.session_state.current_eval_index}" not in st.session_state:
                st.session_state[f"tag_score_{st.session_state.current_eval_index}"] = 3

            if f"evaluation_feedback_{st.session_state.current_eval_index}" not in st.session_state:
                st.session_state[f"evaluation_feedback_{st.session_state.current_eval_index}"] = ""

            # Sliders for scoring
            summary_score = st.slider("Rate the Succinct Summary (1-5)", min_value=1, max_value=5,
                                      key=f'summary_score_{st.session_state.current_eval_index}')
            st.markdown("#### Assigned Tags")
            st.write(current_entry.get('Assigned Tags', ''))
            tag_score = st.slider("Rate the Assigned Tags (1-5)", min_value=1, max_value=5,
                                  key=f'tag_score_{st.session_state.current_eval_index}')
            st.markdown("#### Provide Your Feedback")
            feedback = st.text_area("Feedback", key=f'evaluation_feedback_{st.session_state.current_eval_index}')

            # Submit evaluation
            if st.button("Submit Evaluation"):
                # Save evaluation
                evaluation = {
                    'Evaluator': st.session_state['evaluator_username'],
                    'Summary Score': summary_score,
                    'Tag Score': tag_score,
                    'Feedback': feedback
                }

                # Check if the evaluator has already evaluated this entry
                existing_evaluations = current_entry.get('Evaluations', [])
                updated_evaluations = []

                evaluator_found = False
                previous_summary_score = 0
                previous_tag_score = 0

                for eval in existing_evaluations:
                    if eval['Evaluator'] == st.session_state['evaluator_username']:
                        # Overwrite the existing evaluation with the new one
                        previous_summary_score = eval['Summary Score']
                        previous_tag_score = eval['Tag Score']
                        updated_evaluations.append(evaluation)
                        evaluator_found = True
                    else:
                        updated_evaluations.append(eval)

                # If no previous evaluation was found for this evaluator, append the new evaluation
                if not evaluator_found:
                    updated_evaluations.append(evaluation)

                # Update the entry with the modified evaluations
                current_entry['Evaluations'] = updated_evaluations

                # Update entry in Redis
                institution_manager.update_entry(institution, current_entry)

                # Update cumulative stats in Redis
                stats_key = f"{institution}_stats"
                stats = redis_manager.redis_client.hgetall(stats_key)

                cumulative_summary = float(stats.get('cumulative_summary', 0))
                cumulative_tag = float(stats.get('cumulative_tag', 0))
                total_evaluations = int(stats.get('total_evaluations', 0))

                # If the evaluator has already evaluated the entry, adjust previous scores
                if evaluator_found:
                    cumulative_summary = cumulative_summary - previous_summary_score + summary_score
                    cumulative_tag = cumulative_tag - previous_tag_score + tag_score
                else:
                    cumulative_summary += summary_score
                    cumulative_tag += tag_score
                    total_evaluations += 1

                # Save updated stats back to Redis
                redis_manager.redis_client.hmset(stats_key, {
                    'cumulative_summary': cumulative_summary,
                    'cumulative_tag': cumulative_tag,
                    'total_evaluations': total_evaluations
                })

                st.success("Evaluation submitted successfully!")

                # Move to the next entry
                if st.session_state.current_eval_index < total_assigned_entries - 1:
                    st.session_state.current_eval_index += 1
                    st.rerun()  # Refresh the page to show the next entry
                else:
                    st.success("You have completed all assigned evaluations.")


        if st.button("Logout"):
            st.session_state['evaluator_logged_in'] = False
            st.session_state.pop('assigned_entries', None)
            st.session_state.pop('current_eval_index', None)
            st.success("Logged out successfully!")
            st.rerun()
