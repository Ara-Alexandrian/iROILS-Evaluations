import redis
import psycopg2
import psycopg2.extras
import json
import logging

class DatabaseManager:
    def __init__(self, redis_host, redis_port, psql_host, psql_port, psql_user, psql_password, psql_dbname):
        self.logger = logging.getLogger(__name__)
        # Initialize Redis client
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_client.ping()
            self.logger.info("Connected to Redis successfully.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise e

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
            self.ensure_unique_constraint()  # Ensure unique constraint is created
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

    def ensure_unique_constraint(self):
        """Ensures that the unique constraint for institution and event_number exists."""
        try:
            with self.connection.cursor() as cursor:
                # First, check if the unique constraint already exists
                cursor.execute("""
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE conname = 'unique_institution_event_number';
                """)
                result = cursor.fetchone()

                if not result:
                    # If the constraint does not exist, create it
                    cursor.execute("""
                        ALTER TABLE entries
                        ADD CONSTRAINT unique_institution_event_number UNIQUE (institution, event_number);
                    """)
                    self.logger.info("Unique constraint for institution and event_number created.")
                else:
                    self.logger.info("Unique constraint for institution and event_number already exists.")
        except Exception as e:
            self.logger.error(f"Error ensuring unique constraint on institution and event_number: {e}")
            raise e


    def reset_data(self, institution):
        try:
            st.write(f"Attempting to reset data for institution: {institution}")
            institution_clean = institution.strip().lower()  # Clean the institution name
            # Step 1: Reset Redis data
            st.write("Resetting Redis data...")
            redis_keys_to_delete = [
                f"{institution}:selected_entries",
                f"{institution}:evaluation_scores"
            ]
            deleted_redis = self.redis_client.delete(*redis_keys_to_delete)
            st.write(f"Deleted Redis keys for {institution}. Number of keys deleted: {deleted_redis}")
            self.logger.info(f"Deleted {deleted_redis} Redis keys for {institution}.")
            
            # Step 2: Reset PostgreSQL data
            st.write("Resetting PostgreSQL data...")
            with self.connection.cursor() as cursor:
                # Deleting entries for the institution
                cursor.execute("DELETE FROM entries WHERE LOWER(TRIM(institution)) = %s;", (institution_clean,))
                deleted_entries = cursor.rowcount
                st.write(f"Deleted {deleted_entries} entries for {institution} from PostgreSQL.")
                self.logger.info(f"Deleted {deleted_entries} entries for {institution} from PostgreSQL.")
                
                # Deleting evaluations for the institution
                cursor.execute("DELETE FROM evaluations WHERE LOWER(TRIM(institution)) = %s;", (institution_clean,))
                deleted_evaluations = cursor.rowcount
                st.write(f"Deleted {deleted_evaluations} evaluations for {institution} from PostgreSQL.")
                self.logger.info(f"Deleted {deleted_evaluations} evaluations for {institution} from PostgreSQL.")
                
                # Deleting stats for the institution
                cursor.execute("DELETE FROM institution_stats WHERE LOWER(TRIM(institution)) = %s;", (institution_clean,))
                deleted_stats = cursor.rowcount
                st.write(f"Deleted {deleted_stats} institution stats for {institution} from PostgreSQL.")
                self.logger.info(f"Deleted {deleted_stats} institution stats for {institution} from PostgreSQL.")

            # Step 3: Reset session state
            st.write("Resetting session state...")
            # Call reset_session_state() here if defined, or handle it appropriately
            self.logger.info(f"All data for {institution} has been reset.")
        except Exception as e:
            st.error(f"Error resetting data for {institution}: {e}")
            self.logger.error(f"Error resetting data for {institution}: {e}")





    def get_selected_entries(self, institution):
        try:
            entries_json = self.redis_client.get(f"{institution}:selected_entries")
            if entries_json:
                entries = json.loads(entries_json)
                self.logger.debug(f"Fetched {len(entries)} selected entries for {institution} from Redis.")
                return entries
            else:
                self.logger.debug(f"No selected entries found for {institution} in Redis.")
                return []
        except Exception as e:
            self.logger.error(f"Error fetching selected entries for {institution} from Redis: {e}")
            return []

    def save_selected_entries(self, institution, entries):
        try:
            institution_clean = institution.strip().lower()
            entries_json = json.dumps(entries)
            self.redis_client.set(f"{institution}:selected_entries", entries_json)
            self.logger.info(f"Selected entries for {institution} have been saved in Redis.")

            # Save to PostgreSQL in batch
            with self.connection.cursor() as cursor:
                # Delete existing entries for the institution
                cursor.execute("DELETE FROM entries WHERE LOWER(TRIM(institution)) = %s;", (institution_clean,))
                self.logger.debug(f"Deleted existing entries for {institution} in PostgreSQL.")

                # Prepare data for batch insertion
                values = [
                    (institution_clean, entry.get('Event Number', ''), json.dumps(entry))
                    for entry in entries
                ]

                # Use psycopg2.extras.execute_values for efficient batch insertion
                insert_query = """
                    INSERT INTO entries (institution, event_number, data)
                    VALUES %s
                    ON CONFLICT (institution, event_number)
                    DO UPDATE SET data = EXCLUDED.data;
                """
                psycopg2.extras.execute_values(
                    cursor, insert_query, values, template=None, page_size=100
                )
            self.logger.info(f"Selected entries for {institution} have been saved in PostgreSQL.")
        except Exception as e:
            self.logger.error(f"Error saving selected entries for {institution}: {e}")
            raise e


    def get_evaluation_scores(self, institution):
        try:
            scores_json = self.redis_client.get(f"{institution}:evaluation_scores")
            if scores_json:
                scores = json.loads(scores_json)
                self.logger.debug(f"Fetched evaluation scores for {institution} from Redis.")
                return scores
            else:
                self.logger.debug(f"No evaluation scores found for {institution} in Redis.")
                return {}
        except Exception as e:
            self.logger.error(f"Error fetching evaluation scores for {institution} from Redis: {e}")
            return {}

    def take_snapshot(self, institution):
        try:
            # Save Redis data to a snapshot file
            entries = self.get_selected_entries(institution)
            with open(f"{institution}_snapshot.json", "w") as f:
                json.dump(entries, f)
            self.logger.info(f"Snapshot taken for {institution}.")
        except Exception as e:
            self.logger.error(f"Error taking snapshot for {institution}: {e}")
            raise e

    def load_snapshot(self, institution):
        try:
            # Load Redis data from a snapshot file
            with open(f"{institution}_snapshot.json", "r") as f:
                entries = json.load(f)
            self.save_selected_entries(institution, entries)
            self.logger.info(f"Snapshot loaded for {institution}.")
        except Exception as e:
            self.logger.error(f"Error loading snapshot for {institution}: {e}")
            raise e

    def update_entry(self, institution, updated_entry):
        try:
            # Update entry in PostgreSQL
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE entries
                    SET data = %s
                    WHERE institution = %s AND event_number = %s;
                """, (json.dumps(updated_entry), institution, updated_entry.get('Event Number')))
            self.logger.debug(f"Entry {updated_entry['Event Number']} updated in PostgreSQL.")

            # Update entry in Redis
            entries = self.get_selected_entries(institution)
            for idx, entry in enumerate(entries):
                if entry.get('Event Number') == updated_entry.get('Event Number'):
                    entries[idx] = updated_entry
                    break
            self.redis_client.set(f"{institution}:selected_entries", json.dumps(entries))
            self.logger.debug(f"Entry {updated_entry['Event Number']} updated in Redis.")
        except Exception as e:
            self.logger.error(f"Error updating entry {updated_entry['Event Number']} for {institution}: {e}")
            raise e

    def update_institution_stats(self, institution, summary_score, tag_score, is_new_evaluation, old_summary_score=0, old_tag_score=0):
        try:
            with self.connection.cursor() as cursor:
                if is_new_evaluation:
                    cursor.execute("""
                        INSERT INTO institution_stats (institution, cumulative_summary, cumulative_tag, total_evaluations)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (institution)
                        DO UPDATE SET
                            cumulative_summary = institution_stats.cumulative_summary + EXCLUDED.cumulative_summary,
                            cumulative_tag = institution_stats.cumulative_tag + EXCLUDED.cumulative_tag,
                            total_evaluations = institution_stats.total_evaluations + EXCLUDED.total_evaluations;
                    """, (institution, summary_score, tag_score, 1))
                    self.logger.debug(f"Inserted/Updated institution_stats for {institution} (New Evaluation).")
                else:
                    # Adjust the cumulative scores by subtracting old scores and adding new ones
                    summary_diff = summary_score - old_summary_score
                    tag_diff = tag_score - old_tag_score
                    cursor.execute("""
                        UPDATE institution_stats
                        SET cumulative_summary = cumulative_summary + %s,
                            cumulative_tag = cumulative_tag + %s
                        WHERE institution = %s;
                    """, (summary_diff, tag_diff, institution))
                    self.logger.debug(f"Updated institution_stats for {institution} (Existing Evaluation).")
            self.logger.info(f"Institution stats updated for {institution}.")
        except Exception as e:
            self.logger.error(f"Error updating institution stats for {institution}: {e}")
            raise e

    def get_institution_stats(self, institution):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT cumulative_summary, cumulative_tag, total_evaluations
                    FROM institution_stats
                    WHERE institution = %s;
                """, (institution,))
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

    def get_all_entries(self, institution):
        try:
            # Fetch all entries for the institution from PostgreSQL
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT data
                    FROM entries
                    WHERE institution = %s;
                """, (institution,))
                results = cursor.fetchall()
                entries = [record[0] for record in results]
            self.logger.debug(f"Fetched {len(entries)} all entries for {institution} from PostgreSQL.")
            return entries
        except Exception as e:
            self.logger.error(f"Error fetching all entries for {institution}: {e}")
            return []

    def update_entries_batch(self, institution, entries):
        """Batch update multiple entries in Redis and PostgreSQL."""
        try:
            # Update entries in PostgreSQL
            with self.connection.cursor() as cursor:
                insert_query = """
                    INSERT INTO entries (institution, event_number, data)
                    VALUES %s
                    ON CONFLICT (institution, event_number)
                    DO UPDATE SET data = EXCLUDED.data;
                """
                values = [
                    (institution, entry.get('Event Number', ''), json.dumps(entry))
                    for entry in entries
                ]
                psycopg2.extras.execute_values(
                    cursor, insert_query, values, template=None, page_size=100
                )
            self.logger.debug(f"Batch updated {len(entries)} entries for {institution} in PostgreSQL.")

            # Update entries in Redis
            all_entries = self.get_selected_entries(institution)
            event_number_to_entry = {entry['Event Number']: entry for entry in all_entries}
            for entry in entries:
                event_number = entry.get('Event Number', '')
                if event_number in event_number_to_entry:
                    event_number_to_entry[event_number] = entry
            updated_entries = list(event_number_to_entry.values())
            self.redis_client.set(f"{institution}:selected_entries", json.dumps(updated_entries))
            self.logger.debug(f"Batch updated {len(entries)} entries for {institution} in Redis.")
        except Exception as e:
            self.logger.error(f"Error batch updating entries for {institution}: {e}")
            raise e
