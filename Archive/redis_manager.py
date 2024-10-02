import redis
import json
import logging
import streamlit as st
from time import sleep  # Simulate long-running task

class RedisManager:
    def __init__(self, host, port):
        self.redis_client = redis.StrictRedis(host=host, port=port, db=0, decode_responses=True)

    def get_selected_entries(self, institution):
        """Retrieve selected entries for a specific institution."""
        entries = self.redis_client.get(f"{institution}:selected_entries")
        return json.loads(entries) if entries else []

    def get_evaluation_scores(self, institution):
        """Retrieve evaluation scores for a specific institution."""
        scores = self.redis_client.get(f"{institution}:evaluation_scores")
        return json.loads(scores) if scores else {}

    def save_selected_entries(self, institution, selected_entries):
        """Save selected entries for a specific institution."""
        self.redis_client.set(f"{institution}:selected_entries", json.dumps(selected_entries))

    def save_evaluation_scores(self, institution, evaluation_scores):
        """Save evaluation scores for a specific institution."""
        self.redis_client.set(f"{institution}:evaluation_scores", json.dumps(evaluation_scores))

    def reset_data(self, institution):
        """Reset selected entries and evaluation scores for a specific institution."""
        self.redis_client.delete(f"{institution}:selected_entries")
        self.redis_client.delete(f"{institution}:evaluation_scores")


class RedisSnapshotManager:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    def take_snapshot(self, institution):
        """Take a snapshot of data for a specific institution and store it."""
        try:
            # Retrieve current data for the institution
            selected_entries = self.redis_client.get(f"{institution}:selected_entries")
            evaluation_scores = self.redis_client.get(f"{institution}:evaluation_scores")
            
            # Prepare snapshot data and store it under a specific institution key
            snapshot_data = {
                'selected_entries': selected_entries,
                'evaluation_scores': evaluation_scores
            }

            # Save the snapshot for the institution
            snapshot_key = f"{institution}:snapshot"
            self.redis_client.set(snapshot_key, json.dumps(snapshot_data))
            self.logger.info(f"Snapshot for {institution} saved successfully.")

        except Exception as e:
            self.logger.error(f"Failed to take snapshot for {institution}: {e}")

    def load_snapshot(self, institution):
        """Load a previously taken snapshot for a specific institution."""
        try:
            # Retrieve snapshot for the institution using the institution-specific key
            snapshot_key = f"{institution}:snapshot"
            snapshot_data = self.redis_client.get(snapshot_key)
            
            if snapshot_data:
                snapshot_data = json.loads(snapshot_data)

                # Restore the snapshot data for the specific institution
                self.redis_client.set(f"{institution}:selected_entries", snapshot_data['selected_entries'])
                self.redis_client.set(f"{institution}:evaluation_scores", snapshot_data['evaluation_scores'])
                
                self.logger.info(f"Snapshot for {institution} loaded successfully.")
            else:
                self.logger.warning(f"No snapshot found for {institution}.")

        except Exception as e:
            self.logger.error(f"Failed to load snapshot for {institution}: {e}")



# Inside your Streamlit app where Redis operations happen
def reset_institution(institution, institution_manager):
    # Show a spinner and lock UI
    with st.spinner(f"Resetting data for {institution}. Please wait..."):
        institution_manager.reset_data(institution)
        sleep(1)  # Simulate time taken for Redis operation
        st.success(f"All data for {institution} has been reset.")


# # Updated Reset Button in Streamlit App
# if st.button(f"Reset {institution} Data"):
#     reset_institution(institution, institution_manager)
#     st.rerun()  # Force a page refresh after the reset is complete
