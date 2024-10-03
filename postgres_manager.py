import psycopg2
import json
import logging

class PostgresManager:
    """Manages PostgreSQL operations for selected entries, evaluation scores, and snapshots."""

    def __init__(self, host, port, user, password, database):
        self.logger = logging.getLogger(__name__)
        try:
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            self.connection.autocommit = True
            self.logger.info("PostgreSQL connection established.")
            self.initialize_tables()
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def initialize_tables(self):
        """Initializes the necessary tables for storing entries, evaluations, and snapshots."""
        try:
            with self.connection.cursor() as cursor:
                # Create table for selected entries
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS selected_entries (
                        institution VARCHAR(255) PRIMARY KEY,
                        entries JSONB
                    );
                """)
                
                # Create table for evaluation scores
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evaluation_scores (
                        institution VARCHAR(255) PRIMARY KEY,
                        scores JSONB
                    );
                """)
                
                # Create table for snapshots
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS snapshots (
                        institution VARCHAR(255) PRIMARY KEY,
                        snapshot JSONB
                    );
                """)

                # Create table for institution statistics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS institution_stats (
                        institution VARCHAR(255) PRIMARY KEY,
                        cumulative_summary FLOAT,
                        cumulative_tag FLOAT,
                        total_evaluations INT
                    );
                """)

            self.logger.info("PostgreSQL tables initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL tables: {e}")
            raise

    def save_selected_entries(self, institution, selected_entries):
        """Saves selected entries for an institution."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO selected_entries (institution, entries)
                    VALUES (%s, %s)
                    ON CONFLICT (institution)
                    DO UPDATE SET entries = EXCLUDED.entries;
                """, (institution, json.dumps(selected_entries)))
            self.logger.info(f"Selected entries saved for {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to save selected entries for {institution}: {e}")

    def save_evaluation_scores(self, institution, evaluation_scores):
        """Saves evaluation scores for an institution."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO evaluation_scores (institution, scores)
                    VALUES (%s, %s)
                    ON CONFLICT (institution)
                    DO UPDATE SET scores = EXCLUDED.scores;
                """, (institution, json.dumps(evaluation_scores)))
            self.logger.info(f"Evaluation scores saved for {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to save evaluation scores for {institution}: {e}")

    def reset_institution_data(self, institution):
        """Resets data for an institution."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM selected_entries WHERE institution = %s;", (institution,))
                cursor.execute("DELETE FROM evaluation_scores WHERE institution = %s;", (institution,))
                cursor.execute("DELETE FROM institution_stats WHERE institution = %s;", (institution,))
            self.logger.info(f"All data reset for {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to reset data for {institution}: {e}")

    def save_snapshot(self, institution, snapshot_data):
        """Saves a snapshot for an institution."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO snapshots (institution, snapshot)
                    VALUES (%s, %s)
                    ON CONFLICT (institution)
                    DO UPDATE SET snapshot = EXCLUDED.snapshot;
                """, (institution, json.dumps(snapshot_data)))
            self.logger.info(f"Snapshot saved for {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to save snapshot for {institution}: {e}")

    def load_snapshot(self, institution):
        """Loads a snapshot for an institution."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT snapshot FROM snapshots WHERE institution = %s;", (institution,))
                result = cursor.fetchone()
                if result:
                    return result[0]  # JSON snapshot
                else:
                    self.logger.warning(f"No snapshot found for {institution}.")
                    return None
        except Exception as e:
            self.logger.error(f"Failed to load snapshot for {institution}: {e}")
            return None

    def update_institution_stats(self, institution, cumulative_summary, cumulative_tag, total_evaluations):
        """Updates the cumulative statistics for an institution."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO institution_stats (institution, cumulative_summary, cumulative_tag, total_evaluations)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (institution)
                    DO UPDATE SET 
                        cumulative_summary = EXCLUDED.cumulative_summary,
                        cumulative_tag = EXCLUDED.cumulative_tag,
                        total_evaluations = EXCLUDED.total_evaluations;
                """, (institution, cumulative_summary, cumulative_tag, total_evaluations))
            self.logger.info(f"Institution statistics updated for {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to update institution statistics for {institution}: {e}")

    def get_institution_stats(self, institution):
        """Retrieves the cumulative statistics for an institution."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT cumulative_summary, cumulative_tag, total_evaluations 
                    FROM institution_stats WHERE institution = %s;
                """, (institution,))
                result = cursor.fetchone()
                if result:
                    return {
                        'cumulative_summary': result[0],
                        'cumulative_tag': result[1],
                        'total_evaluations': result[2]
                    }
                else:
                    self.logger.warning(f"No statistics found for {institution}.")
                    return {
                        'cumulative_summary': 0.0,
                        'cumulative_tag': 0.0,
                        'total_evaluations': 0
                    }
        except Exception as e:
            self.logger.error(f"Failed to retrieve statistics for {institution}: {e}")
            return {
                'cumulative_summary': 0.0,
                'cumulative_tag': 0.0,
                'total_evaluations': 0
            }
