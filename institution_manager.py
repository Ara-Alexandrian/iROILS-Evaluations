# institution_manager.py

import json
import logging

class InstitutionManager:
    """Manages institution data stored in Redis."""

    def __init__(self, redis_manager):
        self.redis_manager = redis_manager
        self.redis_client = redis_manager.redis_client
        self.logger = logging.getLogger(__name__)

    def get_all_entries(self, institution):
        """Retrieve all entries for the institution."""
        entries_json = self.redis_client.get(f"{institution}:entries")
        if entries_json:
            try:
                entries = json.loads(entries_json)
                return entries
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error for all entries: {e}")
                return []
        else:
            return []

    def get_selected_entries(self, institution):
        """Retrieve selected entries for the institution."""
        all_entries = self.get_all_entries(institution)
        selected_entries = [entry for entry in all_entries if entry.get('Selected') == 'Select for Evaluation']
        return selected_entries

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

    def get_institution_data(self, institution):
        """Retrieve all entries and evaluation scores for the institution."""
        all_entries = self.get_all_entries(institution)
        evaluation_scores = self.get_evaluation_scores(institution)
        return all_entries, evaluation_scores

    def save_institution_data(self, institution, entries):
        """Save all entries for the institution."""
        try:
            entries_json = json.dumps(entries)
            self.redis_client.set(f"{institution}:entries", entries_json)
        except Exception as e:
            self.logger.error(f"Failed to save institution data: {e}")

    def reset_institution_data(self, institution):
        """Reset all data for the institution in Redis."""
        try:
            self.redis_client.delete(f"{institution}:entries")
            self.redis_client.delete(f"{institution}:evaluation_scores")
            self.logger.info(f"Data for {institution} has been reset in Redis.")
        except Exception as e:
            self.logger.error(f"Failed to reset data for {institution} in Redis: {e}")

    def update_entry(self, institution, updated_entry):
        """Update a single entry for the institution."""
        try:
            entries = self.get_all_entries(institution)
            for idx, entry in enumerate(entries):
                if entry['Event Number'] == updated_entry['Event Number']:
                    entries[idx] = updated_entry
                    break
            else:
                # Entry not found, add it
                entries.append(updated_entry)
            self.save_institution_data(institution, entries)
        except Exception as e:
            self.logger.error(f"Failed to update entry: {e}")

    def update_selection(self, institution, event_number, selection_status):
        """Update the selection status of a specific entry."""
        try:
            entries = self.get_all_entries(institution)
            for entry in entries:
                if entry['Event Number'] == event_number:
                    entry['Selected'] = selection_status
                    break
            self.save_institution_data(institution, entries)
        except Exception as e:
            self.logger.error(f"Failed to update selection: {e}")

    def initialize_entries(self, institution, entries):
        """Initialize entries with default values if necessary and save them."""
        for entry in entries:
            entry.setdefault('Selected', 'Do Not Select')
            entry.setdefault('Evaluation', None)
            entry.setdefault('Assigned Tags', [])
        self.save_institution_data(institution, entries)
