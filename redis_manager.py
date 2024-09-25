# redis_manager.py

import redis
import json
import logging

class RedisManager:
    def __init__(self, host, port):
        self.redis_client = redis.StrictRedis(host=host, port=port, db=0, decode_responses=True)

    def get_selected_entries(self, institution):
        entries = self.redis_client.get(f"{institution}:selected_entries")
        return json.loads(entries) if entries else []

    def get_evaluation_scores(self, institution):
        scores = self.redis_client.get(f"{institution}:evaluation_scores")
        return json.loads(scores) if scores else {}

    def save_selected_entries(self, institution, selected_entries):
        self.redis_client.set(f"{institution}:selected_entries", json.dumps(selected_entries))

    def save_evaluation_scores(self, institution, evaluation_scores):
        self.redis_client.set(f"{institution}:evaluation_scores", json.dumps(evaluation_scores))

    def reset_data(self, institution):
        self.redis_client.delete(f"{institution}:selected_entries")
        self.redis_client.delete(f"{institution}:evaluation_scores")



class RedisSnapshotManager:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    def take_snapshot(self, institution):
        try:
            selected_entries = self.redis_client.get(f"{institution}:selected_entries")
            evaluation_scores = self.redis_client.get(f"{institution}:evaluation_scores")
            
            snapshot_data = {
                'selected_entries': selected_entries,
                'evaluation_scores': evaluation_scores
            }

            # Save snapshot to Redis
            self.redis_client.set(f"{institution}:snapshot", json.dumps(snapshot_data))
            self.logger.info(f"Snapshot for {institution} saved successfully.")

        except Exception as e:
            self.logger.error(f"Failed to take snapshot for {institution}: {e}")

    def load_snapshot(self, institution):
        try:
            snapshot_data = self.redis_client.get(f"{institution}:snapshot")
            if snapshot_data:
                snapshot_data = json.loads(snapshot_data)
                
                self.redis_client.set(f"{institution}:selected_entries", snapshot_data['selected_entries'])
                self.redis_client.set(f"{institution}:evaluation_scores", snapshot_data['evaluation_scores'])
                
                self.logger.info(f"Snapshot for {institution} loaded successfully.")
            else:
                self.logger.warning(f"No snapshot found for {institution}.")

        except Exception as e:
            self.logger.error(f"Failed to load snapshot for {institution}: {e}")