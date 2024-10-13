import json
import logging

class InstitutionManager:
    """Manages institution data stored in Redis and PostgreSQL."""

    def __init__(self, redis_manager, postgres_manager):
        self.redis_manager = redis_manager
        self.postgres_manager = postgres_manager
        self.logger = logging.getLogger(__name__)

    def get_all_entries(self, institution):
        """Retrieve all entries for the institution from Redis."""
        try:
            entries = self.redis_manager.get_selected_entries(institution)
            return entries
        except Exception as e:
            self.logger.error(f"Failed to retrieve entries for {institution}: {e}")
            return []

    def update_entry(self, institution, updated_entry):
        """Update a single entry for the institution in Redis and PostgreSQL."""
        self.redis_manager.update_entry(institution, updated_entry)
        self.logger.info(f"Entry {updated_entry['Event Number']} for {institution} updated in Redis and PostgreSQL.")

    def get_selected_entries(self, institution):
        """Retrieve selected entries for the institution."""
        return self.redis_manager.get_selected_entries(institution)

    def get_evaluation_scores(self, institution):
        """Retrieve evaluation scores for the institution from Redis."""
        return self.redis_manager.get_evaluation_scores(institution)

    def reset_institution_data(self, institution):
        """Reset all data for an institution in both Redis and PostgreSQL."""
        try:
            # Reset Redis data
            self.redis_manager.reset_data(institution)
            self.logger.info(f"Redis data reset for institution {institution}")

            # Reset PostgreSQL data
            self.postgres_manager.reset_institution_data(institution)
            self.logger.info(f"PostgreSQL data reset for institution {institution}")

        except Exception as e:
            self.logger.error(f"Failed to reset data for institution {institution}: {e}")
            raise e

    def save_institution_data(self, institution, entries):
        """Save all entries for the institution in Redis and PostgreSQL."""
        self.redis_manager.save_selected_entries(institution, entries)
        self.logger.info(f"Data for {institution} has been saved in Redis and PostgreSQL.")

    def initialize_entries(self, institution, entries):
        """Initialize entries with default values and save them in Redis and PostgreSQL."""
        try:
            for entry in entries:
                entry.setdefault('Selected', 'Do Not Select')
                entry.setdefault('Evaluation', None)
                entry.setdefault('Assigned Tags', [])

            self.save_institution_data(institution, entries)
            self.logger.info(f"Initialized and saved entries for institution {institution}")
        except Exception as e:
            self.logger.error(f"Failed to initialize entries for institution {institution}: {e}")
            raise e

    def load_from_postgres(self, institution):
        """Load all entries and evaluation scores for the institution from PostgreSQL."""
        try:
            query_entries = """
            SELECT event_number, data FROM entries WHERE institution = %s;
            """
            query_scores = """
            SELECT evaluator, entry_number, summary_score, tag_score, feedback 
            FROM evaluations WHERE institution = %s;
            """
            with self.postgres_manager.connection.cursor() as cursor:
                cursor.execute(query_entries, (institution,))
                entries = cursor.fetchall()

                cursor.execute(query_scores, (institution,))
                evaluation_scores = cursor.fetchall()

            entries_dict = [json.loads(entry[1]) for entry in entries]
            evaluation_scores_dict = {}
            for score in evaluation_scores:
                evaluator, entry_number, summary_score, tag_score, feedback = score
                if entry_number not in evaluation_scores_dict:
                    evaluation_scores_dict[entry_number] = []
                evaluation_scores_dict[entry_number].append({
                    'Evaluator': evaluator,
                    'Summary Score': summary_score,
                    'Tag Score': tag_score,
                    'Feedback': feedback
                })

            return entries_dict, evaluation_scores_dict
        except Exception as e:
            self.logger.error(f"Error loading data from PostgreSQL for institution {institution}: {e}")
            return [], {}
