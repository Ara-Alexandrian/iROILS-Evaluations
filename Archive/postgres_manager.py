import logging
import psycopg2
import json  # Add this import to resolve the error

class PostgresManager:
    """Handles PostgreSQL interactions for institutions, entries, and evaluations."""

    def __init__(self, host, port, user, password, dbname):
        try:
            self.connection = psycopg2.connect(
                host=host, port=port, user=user, password=password, dbname=dbname
            )
            self.logger = logging.getLogger(__name__)
            self.initialize_tables()  # Ensure tables exist at startup
            self.logger.info("PostgreSQL connection established and tables initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to establish PostgreSQL connection: {e}")
            raise e
            
    def initialize_tables(self):
        """Creates required tables in PostgreSQL if they do not exist."""
        try:
            with self.connection.cursor() as cursor:
                # Create entries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entries (
                        id SERIAL PRIMARY KEY,
                        institution VARCHAR(255),
                        event_number INT,
                        data JSONB
                    );
                """)

                # Create evaluations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evaluations (
                        id SERIAL PRIMARY KEY,
                        institution VARCHAR(255),
                        evaluator VARCHAR(255),
                        entry_number INT,
                        summary_score DECIMAL(5, 2),
                        tag_score DECIMAL(5, 2),
                        feedback TEXT
                    );
                """)

                # Commit the changes
                self.connection.commit()
                self.logger.info("Required tables are present in PostgreSQL.")
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL tables: {e}")
            self.connection.rollback()  # Rollback in case of error

    def reset_institution_data(self, institution):
        """Resets data for an institution by clearing the entries and evaluations."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM entries WHERE institution = %s;", (institution,))
                cursor.execute("DELETE FROM evaluations WHERE institution = %s;", (institution,))
                self.connection.commit()
                self.logger.info(f"Data for institution {institution} has been reset.")
        except Exception as e:
            self.logger.error(f"Failed to reset data for institution {institution}: {e}")
            self.connection.rollback()
            raise e

    def save_selected_entries(self, institution, selected_entries):
        """Save selected entries for the institution in PostgreSQL."""
        try:
            with self.connection.cursor() as cursor:
                for entry in selected_entries:
                    cursor.execute("""
                        INSERT INTO entries (institution, event_number, data)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (institution, event_number)
                        DO UPDATE SET data = %s
                    """, (institution, entry['Event Number'], json.dumps(entry), json.dumps(entry)))
                self.connection.commit()
                self.logger.info(f"Selected entries saved for institution {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to save selected entries for institution {institution}: {e}")
            self.connection.rollback()

    def save_evaluation_scores(self, institution, evaluation_scores):
        """Save evaluation scores for the institution in PostgreSQL."""
        try:
            with self.connection.cursor() as cursor:
                for entry_number, evaluations in evaluation_scores.items():
                    for evaluation in evaluations:
                        cursor.execute("""
                            INSERT INTO evaluations (institution, evaluator, entry_number, summary_score, tag_score, feedback)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (institution, evaluator, entry_number)
                            DO UPDATE SET summary_score = %s, tag_score = %s, feedback = %s
                        """, (institution, evaluation['Evaluator'], entry_number, 
                              evaluation['Summary Score'], evaluation['Tag Score'], evaluation['Feedback'],
                              evaluation['Summary Score'], evaluation['Tag Score'], evaluation['Feedback']))
                self.connection.commit()
                self.logger.info(f"Evaluation scores saved for institution {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to save evaluation scores for institution {institution}: {e}")
            self.connection.rollback()

    def get_selected_entries(self, institution):
        """Retrieve selected entries for a specific institution from PostgreSQL."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT event_number, data FROM entries WHERE institution = %s;", (institution,))
                result = cursor.fetchall()
                selected_entries = [json.loads(row[1]) for row in result]
                self.logger.info(f"Selected entries retrieved for institution {institution}.")
                return selected_entries
        except Exception as e:
            self.logger.error(f"Failed to retrieve selected entries for institution {institution}: {e}")
            return []

    def get_evaluation_scores(self, institution):
        """Retrieve evaluation scores for a specific institution from PostgreSQL."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT evaluator, entry_number, summary_score, tag_score, feedback 
                    FROM evaluations WHERE institution = %s;
                """, (institution,))
                result = cursor.fetchall()
                evaluation_scores = {}
                for row in result:
                    entry_number = row[1]
                    if entry_number not in evaluation_scores:
                        evaluation_scores[entry_number] = []
                    evaluation_scores[entry_number].append({
                        'Evaluator': row[0],
                        'Summary Score': row[2],
                        'Tag Score': row[3],
                        'Feedback': row[4]
                    })
                self.logger.info(f"Evaluation scores retrieved for institution {institution}.")
                return evaluation_scores
        except Exception as e:
            self.logger.error(f"Failed to retrieve evaluation scores for institution {institution}: {e}")
            return {}

    def update_institution_stats(self, institution, cumulative_summary, cumulative_tag, total_evaluations):
        """Update or insert institution statistics in PostgreSQL."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO institution_stats (institution, cumulative_summary, cumulative_tag, total_evaluations)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (institution)
                    DO UPDATE SET cumulative_summary = %s, cumulative_tag = %s, total_evaluations = %s
                """, (institution, cumulative_summary, cumulative_tag, total_evaluations,
                      cumulative_summary, cumulative_tag, total_evaluations))
                self.connection.commit()
                self.logger.info(f"Institution stats updated for institution {institution}.")
        except Exception as e:
            self.logger.error(f"Failed to update institution stats for {institution}: {e}")
            self.connection.rollback()

    def get_institution_stats(self, institution):
        """Retrieve institution statistics from PostgreSQL."""
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
                    self.logger.warning(f"No stats found for institution {institution}.")
                    return {
                        'cumulative_summary': 0.0,
                        'cumulative_tag': 0.0,
                        'total_evaluations': 0
                    }
        except Exception as e:
            self.logger.error(f"Failed to retrieve institution stats for {institution}: {e}")
            return {
                'cumulative_summary': 0.0,
                'cumulative_tag': 0.0,
                'total_evaluations': 0
            }
