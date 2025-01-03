# redis_manager.py
      
import redis
import json
import logging
from postgres_manager import PostgresManager

class RedisManager:
    """Manages Redis operations for selected entries and evaluation scores."""
    
    def __init__(self, host, port, postgres_manager):
        self.redis_client = redis.StrictRedis(
            host=host, port=port, db=0, decode_responses=True
        )
        self.postgres_manager = postgres_manager  # Store PostgresManager
        self.logger = logging.getLogger(__name__)

    def get_selected_entries(self, institution):
        """Retrieve selected entries for a specific institution."""
        try:
            entries_json = self.redis_client.get(f"{institution}:selected_entries")
            if entries_json:
                entries = json.loads(entries_json)
                self.logger.info(f"Entries successfully retrieved from Redis for {institution}.")
                return entries
            else:
                # Fallback to PostgreSQL if Redis is unavailable
                self.logger.warning(f"Redis is empty, falling back to PostgreSQL for {institution}.")
                return self.postgres_manager.get_selected_entries(institution)
        except Exception as e:
            self.logger.error(f"Error retrieving selected entries for {institution}: {e}")
            return []


    def update_entry(self, institution, updated_entry):
        """Update a single entry for the institution in Redis and PostgreSQL."""
        try:
            # Fetch and update entries from Redis or PostgreSQL
            entries = self.get_selected_entries(institution)

            # Update or append the entry
            for idx, entry in enumerate(entries):
                if entry['Event Number'] == updated_entry['Event Number']:
                    entries[idx] = updated_entry
                    break
            else:
                entries.append(updated_entry)

            # Save back to Redis and PostgreSQL
            self.save_selected_entries(institution, entries)
            self.logger.info(f"Entry {updated_entry['Event Number']} for {institution} updated successfully.")
        except Exception as e:
            self.logger.error(f"Failed to update entry {updated_entry['Event Number']} for {institution}: {e}")
            raise e

    def save_selected_entries(self, institution, selected_entries):
        """Save selected entries for a specific institution to Redis and PostgreSQL."""
        try:
            entries_json = json.dumps(selected_entries)
            self.redis_client.set(f"{institution}:selected_entries", entries_json)
            self.postgres_manager.save_selected_entries(institution, selected_entries)
            self.logger.info(f"Selected entries for {institution} saved to Redis and PostgreSQL.")
        except Exception as e:
            self.logger.error(f"Failed to save selected entries for {institution}: {e}")


    def get_evaluation_scores(self, institution):
        """Retrieve evaluation scores for a specific institution."""
        try:
            scores_json = self.redis_client.get(f"{institution}:evaluation_scores")
            if scores_json:
                return json.loads(scores_json)
            else:
                # Fallback to PostgreSQL if Redis is unavailable
                self.logger.warning(f"Failed to fetch from Redis, falling back to PostgreSQL for {institution}.")
                return self.postgres_manager.get_evaluation_scores(institution)
        except Exception as e:
            self.logger.error(f"Error retrieving evaluation scores for {institution}: {e}")
            return {}

    def save_evaluation_scores(self, institution, evaluation_scores):
        """Save evaluation scores for a specific institution."""
        try:
            scores_json = json.dumps(evaluation_scores)
            self.redis_client.set(f"{institution}:evaluation_scores", scores_json)
            # Also save to PostgreSQL for backup
            self.postgres_manager.save_evaluation_scores(institution, evaluation_scores)
        except Exception as e:
            self.logger.error(f"Failed to save evaluation scores for {institution}: {e}")

    def reset_data(self, institution):
        """Reset selected entries and evaluation scores for a specific institution."""
        try:
            self.redis_client.delete(f"{institution}:selected_entries")
            self.redis_client.delete(f"{institution}:evaluation_scores")
            # Also reset the data in PostgreSQL
            self.postgres_manager.reset_data(institution)
            self.logger.info(f"Data for {institution} has been reset.")
        except Exception as e:
            self.logger.error(f"Failed to reset data for {institution}: {e}")

    def update_institution_stats(self, institution, summary_score, tag_score, is_new_evaluation=True, old_summary_score=0, old_tag_score=0):
        """Update the cumulative statistics for an institution."""
        stats_key = f"{institution}_stats"

        # Use Redis transactions to ensure atomic updates
        with self.redis_client.pipeline() as pipe:
            while True:
                try:
                    # Watch the stats_key
                    pipe.watch(stats_key)

                    # Get existing stats or initialize them
                    existing_stats = pipe.hgetall(stats_key)
                    if existing_stats:
                        cumulative_summary = float(existing_stats.get('cumulative_summary', 0))
                        cumulative_tag = float(existing_stats.get('cumulative_tag', 0))
                        total_evaluations = int(existing_stats.get('total_evaluations', 0))
                    else:
                        cumulative_summary = 0.0
                        cumulative_tag = 0.0
                        total_evaluations = 0

                    # Adjust stats
                    cumulative_summary = cumulative_summary - old_summary_score + summary_score
                    cumulative_tag = cumulative_tag - old_tag_score + tag_score

                    if is_new_evaluation:
                        total_evaluations += 1
                    # If it's an update, total_evaluations remains the same

                    # Start transaction
                    pipe.multi()

                    # Save updated stats back to Redis
                    pipe.hmset(stats_key, {
                        'cumulative_summary': cumulative_summary,
                        'cumulative_tag': cumulative_tag,
                        'total_evaluations': total_evaluations
                    })

                    # Execute transaction
                    pipe.execute()

                    # Also save institution stats in PostgreSQL
                    self.postgres_manager.update_institution_stats(
                        institution, cumulative_summary, cumulative_tag, total_evaluations
                    )

                    break
                except redis.WatchError:
                    # If WatchError is raised, it means that the watched key was modified
                    continue  # Retry the transaction

    def get_institution_stats(self, institution):
        """Retrieve the cumulative statistics for an institution."""
        stats_key = f"{institution}_stats"
        try:
            stats = self.redis_client.hgetall(stats_key)
            if stats:
                return {
                    'cumulative_summary': float(stats.get('cumulative_summary', 0)),
                    'cumulative_tag': float(stats.get('cumulative_tag', 0)),
                    'total_evaluations': int(stats.get('total_evaluations', 0))
                }
            else:
                # Fallback to PostgreSQL if Redis data is not available
                return self.postgres_manager.get_institution_stats(institution)
        except Exception as e:
            self.logger.error(f"Failed to get institution stats for {institution}: {e}")
            return {
                'cumulative_summary': 0.0,
                'cumulative_tag': 0.0,
                'total_evaluations': 0
            }


class RedisSnapshotManager:
    """Manages snapshots of Redis data for institutions."""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    def take_snapshot(self, institution):
        """Take a snapshot of data for a specific institution and store it."""
        try:
            # Retrieve and serialize current data for the institution
            selected_entries_json = self.redis_client.get(f"{institution}:selected_entries")
            evaluation_scores_json = self.redis_client.get(f"{institution}:evaluation_scores")

            selected_entries = json.loads(selected_entries_json) if selected_entries_json else []
            evaluation_scores = json.loads(evaluation_scores_json) if evaluation_scores_json else {}

            # Prepare snapshot data
            snapshot_data = {
                'selected_entries': selected_entries,
                'evaluation_scores': evaluation_scores
            }

            # Save the snapshot in Redis
            snapshot_json = json.dumps(snapshot_data)
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

                # Restore the data for the specific institution
                self.redis_client.set(f"{institution}:selected_entries", json.dumps(snapshot_data['selected_entries']))
                self.redis_client.set(f"{institution}:evaluation_scores", json.dumps(snapshot_data['evaluation_scores']))
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
        # Reset entries and evaluations for the institution
        institution_manager.reset_data(institution)

        # Also reset cumulative statistics for the institution
        stats_key = f"{institution}_stats"
        redis_client = institution_manager.redis_manager.redis_client
        redis_client.delete(stats_key)  # Clear stats

        sleep(1)  # Simulate time taken for Redis operation

        # Clear session state related to the institution
        st.session_state.pop('selected_entries', None)
        st.session_state.pop('total_entries', None)
        st.session_state.pop('current_index', None)
        st.success(f"All data for {institution} has been reset.")
