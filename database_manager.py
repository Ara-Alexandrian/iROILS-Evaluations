import psycopg2
import psycopg2.extras
import json
import logging

class DatabaseManager:
    def __init__(self, psql_host, psql_port, psql_user, psql_password, psql_dbname):
        self.logger = logging.getLogger(__name__)

        # Initialize PostgreSQL connection
        try:
            self.connection = psycopg2.connect(
                host=psql_host,
                port=psql_port,
                user=psql_user,
                password=psql_password,
                dbname=psql_dbname
            )
            self.connection.autocommit = True
            self.logger.info("Connected to PostgreSQL successfully.")
            self.initialize_postgresql_tables()
            self.ensure_unique_constraints()  # Ensure unique constraints are created
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise e

    def initialize_postgresql_tables(self):
        try:
            with self.connection.cursor() as cursor:
                # Create entries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entries (
                        id SERIAL PRIMARY KEY,
                        institution VARCHAR(255),
                        event_number VARCHAR(255),
                        data JSONB
                    );
                """)
                # Create evaluations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evaluations (
                        id SERIAL PRIMARY KEY,
                        institution VARCHAR(255),
                        evaluator VARCHAR(255),
                        entry_number VARCHAR(255),
                        summary_score INTEGER,
                        tag_score INTEGER,
                        feedback TEXT
                    );
                """)
                # Create institution_stats table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS institution_stats (
                        institution VARCHAR(255) PRIMARY KEY,
                        cumulative_summary FLOAT,
                        cumulative_tag FLOAT,
                        total_evaluations INTEGER
                    );
                """)
            self.logger.info("PostgreSQL tables initialized successfully.")
        except Exception as e:
            self.logger.error(f"Error initializing PostgreSQL tables: {e}")
            raise e

    def ensure_unique_constraints(self):
        """Ensures that the unique constraints for entries and evaluations exist."""
        try:
            with self.connection.cursor() as cursor:
                # Ensure unique constraint on entries (institution, event_number)
                cursor.execute("""
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE conname = 'unique_institution_event_number';
                """)
                result = cursor.fetchone()
                if not result:
                    cursor.execute("""
                        ALTER TABLE entries
                        ADD CONSTRAINT unique_institution_event_number UNIQUE (institution, event_number);
                    """)
                    self.logger.info("Unique constraint for institution and event_number created.")
                else:
                    self.logger.info("Unique constraint for institution and event_number already exists.")

                # Ensure unique constraint on evaluations (institution, evaluator, entry_number)
                cursor.execute("""
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE conname = 'unique_evaluation';
                """)
                result = cursor.fetchone()
                if not result:
                    cursor.execute("""
                        ALTER TABLE evaluations
                        ADD CONSTRAINT unique_evaluation UNIQUE (institution, evaluator, entry_number);
                    """)
                    self.logger.info("Unique constraint for evaluations created.")
                else:
                    self.logger.info("Unique constraint for evaluations already exists.")
        except Exception as e:
            self.logger.error(f"Error ensuring unique constraints: {e}")
            raise e

    def reset_data(self, institution):
        try:
            institution_clean = institution.strip().lower()
            self.logger.info(f"Attempting to reset data for institution: {institution_clean}")

            with self.connection.cursor() as cursor:
                # Deleting entries for the institution
                cursor.execute("DELETE FROM entries WHERE LOWER(TRIM(institution)) = %s;", (institution_clean,))
                deleted_entries = cursor.rowcount
                self.logger.info(f"Deleted {deleted_entries} entries for {institution_clean} from PostgreSQL.")

                # Deleting evaluations for the institution
                cursor.execute("DELETE FROM evaluations WHERE LOWER(TRIM(institution)) = %s;", (institution_clean,))
                deleted_evaluations = cursor.rowcount
                self.logger.info(f"Deleted {deleted_evaluations} evaluations for {institution_clean} from PostgreSQL.")

                # Deleting stats for the institution
                cursor.execute("DELETE FROM institution_stats WHERE LOWER(TRIM(institution)) = %s;", (institution_clean,))
                deleted_stats = cursor.rowcount
                self.logger.info(f"Deleted {deleted_stats} institution stats for {institution_clean} from PostgreSQL.")

            self.logger.info(f"All data for {institution_clean} has been reset.")
        except Exception as e:
            self.logger.error(f"Error resetting data for {institution_clean}: {e}")
            raise e

    def get_selected_entries(self, institution):
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT data
                    FROM entries
                    WHERE LOWER(TRIM(institution)) = %s;
                """, (institution_clean,))
                results = cursor.fetchall()
                entries = [record['data'] for record in results]
                self.logger.debug(f"Fetched {len(entries)} selected entries for {institution_clean} from PostgreSQL.")
                return entries
        except Exception as e:
            self.logger.error(f"Error fetching selected entries for {institution}: {e}")
            return []

    def save_selected_entries(self, institution, entries):
        try:
            with self.connection.cursor() as cursor:
                for entry in entries:
                    event_number = entry.get('Event Number')
                    if event_number is None:
                        continue  # Skip entries without an Event Number

                    # Convert entry to JSON string
                    json_data = json.dumps(entry)

                    # Insert or update the entry
                    cursor.execute("""
                        INSERT INTO entries (institution, event_number, data)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (institution, event_number) DO UPDATE
                        SET data = EXCLUDED.data;
                    """, (institution.lower(), event_number, json_data))

            self.connection.commit()
            self.logger.debug(f"Inserted/Updated {len(entries)} entries for institution {institution}.")
        except Exception as e:
            self.logger.error(f"Error saving selected entries: {e}")
            raise e  # Reraise exception to be handled by the calling function


    def update_entry(self, institution, updated_entry):
        try:
            institution_clean = institution.strip().lower()
            # Update entry in PostgreSQL
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE entries
                    SET data = %s
                    WHERE LOWER(TRIM(institution)) = %s AND event_number = %s;
                """, (json.dumps(updated_entry), institution_clean, updated_entry.get('Event Number')))
            self.logger.debug(f"Entry {updated_entry['Event Number']} updated in PostgreSQL.")
        except Exception as e:
            self.logger.error(f"Error updating entry {updated_entry['Event Number']} for {institution_clean}: {e}")
            raise e

    def update_entries_batch(self, institution, entries):
        """Batch update multiple entries in PostgreSQL."""
        try:
            institution_clean = institution.strip().lower()

            # Update entries in PostgreSQL
            with self.connection.cursor() as cursor:
                insert_query = """
                    INSERT INTO entries (institution, event_number, data)
                    VALUES %s
                    ON CONFLICT (institution, event_number)
                    DO UPDATE SET data = EXCLUDED.data;
                """
                values = [
                    (institution_clean, entry.get('Event Number', ''), json.dumps(entry))
                    for entry in entries
                ]
                psycopg2.extras.execute_values(
                    cursor, insert_query, values, template=None, page_size=100
                )
            self.logger.debug(f"Batch updated {len(entries)} entries for {institution_clean} in PostgreSQL.")
        except Exception as e:
            self.logger.error(f"Error batch updating entries for {institution_clean}: {e}")
            raise e

    def get_evaluation(self, evaluator, entry_number, institution):
        # Ensure the query matches both the evaluator, entry number, and institution
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT *
                    FROM evaluations
                    WHERE evaluator = %s AND entry_number = %s AND LOWER(TRIM(institution)) = %s;
                """, (evaluator, entry_number, institution_clean))
                result = cursor.fetchone()
                if result:
                    return dict(result)  # return evaluation if found
                else:
                    return None  # return None if no evaluation found
        except Exception as e:
            self.logger.error(f"Error fetching evaluation for evaluator {evaluator}, entry {entry_number}: {e}")
            return None


    def save_evaluation(self, evaluator, entry_number, institution, summary_score, tag_score, feedback):
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor() as cursor:
                # Use UPSERT to insert or update the evaluation
                cursor.execute("""
                    INSERT INTO evaluations (institution, evaluator, entry_number, summary_score, tag_score, feedback)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (institution, evaluator, entry_number)
                    DO UPDATE SET summary_score = EXCLUDED.summary_score,
                                  tag_score = EXCLUDED.tag_score,
                                  feedback = EXCLUDED.feedback;
                """, (institution_clean, evaluator, entry_number, summary_score, tag_score, feedback))
            self.logger.debug(f"Saved evaluation for evaluator {evaluator}, entry {entry_number}.")
        except Exception as e:
            self.logger.error(f"Error saving evaluation for evaluator {evaluator}, entry {entry_number}: {e}")
            raise e

    def update_institution_stats(self, institution, summary_score, tag_score, is_new_evaluation, old_summary_score=0, old_tag_score=0):
        try:
            summary_score = float(summary_score)
            old_summary_score = float(old_summary_score)
            summary_diff = summary_score - old_summary_score
            tag_score = float(tag_score)
            old_tag_score = float(old_tag_score)
            tag_diff = tag_score - old_tag_score

            with self.connection.cursor() as cursor:
                if is_new_evaluation:
                    cursor.execute("""
                        INSERT INTO institution_stats (institution, cumulative_summary, cumulative_tag, total_evaluations)
                        VALUES (%s, %s, %s, 1)
                        ON CONFLICT (institution)
                        DO UPDATE SET 
                            cumulative_summary = institution_stats.cumulative_summary + EXCLUDED.cumulative_summary,
                            cumulative_tag = institution_stats.cumulative_tag + EXCLUDED.cumulative_tag,
                            total_evaluations = institution_stats.total_evaluations + 1;
                    """, (institution, summary_score, tag_score))
                else:
                    cursor.execute("""
                        UPDATE institution_stats
                        SET cumulative_summary = cumulative_summary + %s,
                            cumulative_tag = cumulative_tag + %s
                        WHERE institution = %s;
                    """, (summary_diff, tag_diff, institution))
            self.logger.info(f"Updated stats for {institution} after evaluation.")
        except Exception as e:
            self.logger.error(f"Error updating institution stats for {institution}: {e}")
            raise e


    def get_institution_stats(self, institution):
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT cumulative_summary, cumulative_tag, total_evaluations
                    FROM institution_stats
                    WHERE LOWER(TRIM(institution)) = %s;
                """, (institution_clean,))
                result = cursor.fetchone()
                if result:
                    cumulative_summary, cumulative_tag, total_evaluations = result
                    self.logger.debug(f"Fetched institution stats for {institution}.")
                    return {
                        'cumulative_summary': cumulative_summary,
                        'cumulative_tag': cumulative_tag,
                        'total_evaluations': total_evaluations
                    }
                else:
                    self.logger.debug(f"No institution stats found for {institution}.")
                    return {
                        'cumulative_summary': 0.0,
                        'cumulative_tag': 0.0,
                        'total_evaluations': 0
                    }
        except Exception as e:
            self.logger.error(f"Error fetching institution stats for {institution}: {e}")
            return {
                'cumulative_summary': 0.0,
                'cumulative_tag': 0.0,
                'total_evaluations': 0
            }


    def count_evaluations_by_evaluator(self, evaluator_username, institution):
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM evaluations
                    WHERE evaluator = %s AND LOWER(TRIM(institution)) = %s;
                """, (evaluator_username, institution_clean))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Error counting evaluations for evaluator {evaluator_username}: {e}")
            return 0

    def get_evaluations_by_evaluator(self, evaluator_username, entry_number):
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT summary_score, tag_score, feedback
                    FROM evaluations
                    WHERE evaluator = %s AND entry_number = %s;
                """, (evaluator_username, entry_number))
                evaluations = cursor.fetchall()
                return evaluations
        except Exception as e:
            self.logger.error(f"Failed to fetch evaluations for {evaluator_username} on event {entry_number}: {e}")
            return []

    def check_selected_status(self, institution):
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT data->>'Selected' AS selected_status, COUNT(*)
                    FROM entries
                    WHERE LOWER(TRIM(institution)) = %s
                    GROUP BY selected_status;
                """, (institution_clean,))
                results = cursor.fetchall()
                for status, count in results:
                    self.logger.info(f"Selected status '{status}': {count} entries")
        except Exception as e:
            self.logger.error(f"Error checking selected status for {institution}: {e}")

    def get_all_entries(self, institution):
        return self.get_selected_entries(institution)

    def get_all_evaluators(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT evaluator
                    FROM evaluations
                    ORDER BY evaluator;
                """)
                results = cursor.fetchall()
                evaluators = [row[0] for row in results]
                self.logger.debug(f"Fetched evaluators: {evaluators}")
                return evaluators
        except Exception as e:
            self.logger.error(f"Error fetching evaluator names: {e}")
            return []

    def insert_entry(self, institution, event_number, data_json):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO entries (institution, event_number, data)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (institution, event_number) DO UPDATE
                    SET data = EXCLUDED.data;
                """, (institution, event_number, data_json))
                self.connection.commit()
                self.logger.debug(f"Inserted/Updated entry for event number {event_number} in institution {institution}.")
        except Exception as e:
            self.logger.error(f"Error inserting entry: {e}")
            raise e  # Reraise exception to be caught in the calling function


    def get_user_stats(self, evaluator_username, institution):
        try:
            with self.connection.cursor() as cursor:
                query = """
                    SELECT COUNT(*), AVG(summary_score), AVG(tag_score)
                    FROM evaluations
                    WHERE evaluator = %s AND LOWER(TRIM(institution)) = %s
                """
                cursor.execute(query, (evaluator_username, institution))
                result = cursor.fetchone()
                if result:
                    return {
                        'total_evaluations': result[0],
                        'average_summary_score': result[1],
                        'average_tag_score': result[2]
                    }
                else:
                    return {
                        'total_evaluations': 0,
                        'average_summary_score': 0,
                        'average_tag_score': 0
                    }
        except Exception as e:
            self.logger.error(f"Error fetching user stats for {evaluator_username}: {e}")
            return {
                'total_evaluations': 0,
                'average_summary_score': 0,
                'average_tag_score': 0
            }
