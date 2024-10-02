# redis_manager.py

import redis
import json
import logging
import streamlit as st
from time import sleep  # Simulate long-running tasks

class RedisManager:
    """Manages Redis operations for selected entries and evaluation scores."""

    def __init__(self, host, port):
        self.redis_client = redis.StrictRedis(
            host=host, port=port, db=0, decode_responses=True
        )
        self.logger = logging.getLogger(__name__)

    def get_selected_entries(self, institution):
        """Retrieve selected entries for a specific institution."""
        entries_json = self.redis_client.get(f"{institution}:selected_entries")
        if entries_json:
            try:
                entries = json.loads(entries_json)
                return entries
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error for selected entries: {e}")
                return []
        else:
            return []

    def get_evaluation_scores(self, institution):
        """Retrieve evaluation scores for a specific institution."""
        scores_json = self.redis_client.get(f"{institution}:evaluation_scores")
        if scores_json:
            try:
                scores = json.loads(scores_json)
                return scores
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error for evaluation scores: {e}")
                return {}
        else:
            return {}

    def save_selected_entries(self, institution, selected_entries):
        """Save selected entries for a specific institution."""
        try:
            entries_json = json.dumps(selected_entries)
            self.redis_client.set(f"{institution}:selected_entries", entries_json)
        except Exception as e:
            self.logger.error(f"Failed to save selected entries: {e}")

    def save_evaluation_scores(self, institution, evaluation_scores):
        """Save evaluation scores for a specific institution."""
        try:
            scores_json = json.dumps(evaluation_scores)
            self.redis_client.set(f"{institution}:evaluation_scores", scores_json)
        except Exception as e:
            self.logger.error(f"Failed to save evaluation scores: {e}")

    def reset_data(self, institution):
        """Reset selected entries and evaluation scores for a specific institution."""
        try:
            self.redis_client.delete(f"{institution}:selected_entries")
            self.redis_client.delete(f"{institution}:evaluation_scores")
            self.logger.info(f"Data for {institution} has been reset.")
        except Exception as e:
            self.logger.error(f"Failed to reset data for {institution}: {e}")

class RedisSnapshotManager:
    """Manages snapshots of Redis data for institutions."""

    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    def take_snapshot(self, institution):
        """Take a snapshot of data for a specific institution and store it."""
        try:
            # Retrieve and deserialize current data for the institution
            selected_entries_json = self.redis_client.get(f"{institution}:selected_entries")
            evaluation_scores_json = self.redis_client.get(f"{institution}:evaluation_scores")

            selected_entries = json.loads(selected_entries_json) if selected_entries_json else []
            evaluation_scores = json.loads(evaluation_scores_json) if evaluation_scores_json else {}

            # Prepare snapshot data as a dictionary
            snapshot_data = {
                'selected_entries': selected_entries,
                'evaluation_scores': evaluation_scores
            }

            # Serialize the snapshot data
            snapshot_json = json.dumps(snapshot_data)

            # Save the snapshot for the institution
            snapshot_key = f"{institution}:snapshot"
            self.redis_client.set(snapshot_key, snapshot_json)
            self.logger.info(f"Snapshot for {institution} saved successfully.")

        except Exception as e:
            self.logger.error(f"Failed to take snapshot for {institution}: {e}")
            st.error(f"Failed to take snapshot for {institution}. Please check logs for details.")

    def load_snapshot(self, institution):
        """Load a previously taken snapshot for a specific institution."""
        try:
            # Retrieve the snapshot
            snapshot_key = f"{institution}:snapshot"
            snapshot_json = self.redis_client.get(snapshot_key)

            if snapshot_json:
                # Deserialize the snapshot data
                snapshot_data = json.loads(snapshot_json)

                # Serialize individual components to store back in Redis
                selected_entries_json = json.dumps(snapshot_data['selected_entries'])
                evaluation_scores_json = json.dumps(snapshot_data['evaluation_scores'])

                # Restore the data for the specific institution
                self.redis_client.set(f"{institution}:selected_entries", selected_entries_json)
                self.redis_client.set(f"{institution}:evaluation_scores", evaluation_scores_json)

                self.logger.info(f"Snapshot for {institution} loaded successfully.")
            else:
                self.logger.warning(f"No snapshot found for {institution}.")
                st.warning(f"No snapshot found for {institution}.")

        except Exception as e:
            self.logger.error(f"Failed to load snapshot for {institution}: {e}")
            st.error(f"Failed to load snapshot for {institution}. Please check logs for details.")

# Function to reset institution data within your Streamlit app
def reset_institution(institution, institution_manager):
    """Resets the data for the given institution and updates the session state."""
    with st.spinner(f"Resetting data for {institution}. Please wait..."):
        institution_manager.reset_data(institution)
        sleep(1)  # Simulate time taken for Redis operation
        # Clear session state related to the institution
        st.session_state.pop('selected_entries', None)
        st.session_state.pop('total_entries', None)
        st.session_state.pop('current_index', None)
        st.success(f"All data for {institution} has been reset.")
