"""
Database service for the iROILS Evaluations application.

This module provides a service for interacting with the PostgreSQL database,
abstracting the database operations and providing a clean interface.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple, Union
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection, cursor

from app.models.entry import Entry
from app.models.evaluation import Evaluation
from app.models.institution import InstitutionStats
from app.exceptions.db_exceptions import (
    ConnectionError, 
    QueryError, 
    IntegrityError,
    RecordNotFoundError
)


class DatabaseService:
    """
    Service for database operations.
    
    This class provides methods for interacting with the PostgreSQL database,
    handling connections, transactions, and CRUD operations for entities.
    """
    
    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        """
        Initialize the database service.
        
        Args:
            host (str): Database host address
            port (int): Database port
            user (str): Database user
            password (str): Database password
            dbname (str): Database name
            
        Raises:
            ConnectionError: If the connection to the database fails
        """
        self.logger = logging.getLogger(__name__)
        self.connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'dbname': dbname
        }
        
        # Initialize database connection
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            self.connection.autocommit = True
            self.logger.info("Connected to PostgreSQL successfully.")
            
            # Initialize database schema
            self._initialize_schema()
        except Exception as e:
            error = ConnectionError(
                host=host, 
                port=port, 
                db_name=dbname, 
                message=f"Failed to connect to PostgreSQL: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    def _initialize_schema(self) -> None:
        """
        Initialize the database schema if it doesn't exist.
        
        Creates tables and constraints for entries, evaluations, and institution stats.
        
        Raises:
            QueryError: If schema initialization fails
        """
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
                
                # Ensure unique constraints
                self._ensure_unique_constraints(cursor)
                
            self.logger.info("PostgreSQL schema initialized successfully.")
        except Exception as e:
            error = QueryError(message=f"Error initializing PostgreSQL schema: {e}")
            self.logger.error(str(error))
            raise error from e
    
    def _ensure_unique_constraints(self, cursor: cursor) -> None:
        """
        Ensure unique constraints exist for tables.
        
        Args:
            cursor (cursor): Database cursor
            
        Raises:
            QueryError: If constraint creation fails
        """
        try:
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
        except Exception as e:
            error = QueryError(message=f"Error ensuring unique constraints: {e}")
            self.logger.error(str(error))
            raise error from e
    
    def reset_institution_data(self, institution: str) -> None:
        """
        Reset all data for an institution.
        
        Args:
            institution (str): The institution to reset data for
            
        Raises:
            QueryError: If data reset fails
        """
        try:
            institution_clean = institution.strip().lower()
            self.logger.info(f"Resetting data for institution: {institution_clean}")
            
            with self.connection.cursor() as cursor:
                # Delete entries for the institution
                cursor.execute(
                    "DELETE FROM entries WHERE LOWER(TRIM(institution)) = %s;", 
                    (institution_clean,)
                )
                deleted_entries = cursor.rowcount
                
                # Delete evaluations for the institution
                cursor.execute(
                    "DELETE FROM evaluations WHERE LOWER(TRIM(institution)) = %s;", 
                    (institution_clean,)
                )
                deleted_evaluations = cursor.rowcount
                
                # Delete stats for the institution
                cursor.execute(
                    "DELETE FROM institution_stats WHERE LOWER(TRIM(institution)) = %s;", 
                    (institution_clean,)
                )
                deleted_stats = cursor.rowcount
            
            self.logger.info(
                f"Reset completed - deleted {deleted_entries} entries, "
                f"{deleted_evaluations} evaluations, and {deleted_stats} stats "
                f"for {institution_clean}"
            )
        except Exception as e:
            error = QueryError(message=f"Error resetting data for {institution}: {e}")
            self.logger.error(str(error))
            raise error from e
    
    # Entry operations
    
    def get_entries(self, institution: str, selected_only: bool = False) -> List[Entry]:
        """
        Get entries for an institution.
        
        Args:
            institution (str): The institution to get entries for
            selected_only (bool): Whether to get only selected entries
            
        Returns:
            List[Entry]: List of entries
            
        Raises:
            QueryError: If query execution fails
        """
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if selected_only:
                    # Get only selected entries
                    cursor.execute("""
                        SELECT institution, event_number, data
                        FROM entries
                        WHERE LOWER(TRIM(institution)) = %s
                          AND data->>'Selected' != 'Do Not Select';
                    """, (institution_clean,))
                else:
                    # Get all entries
                    cursor.execute("""
                        SELECT institution, event_number, data
                        FROM entries
                        WHERE LOWER(TRIM(institution)) = %s;
                    """, (institution_clean,))
                
                rows = cursor.fetchall()
                entries = []
                
                for row in rows:
                    # Convert row to Entry object
                    data = row['data']
                    entry = Entry(
                        institution=institution_clean,
                        event_number=row['event_number'],
                        data=data,
                        selected=data.get('Selected', 'Do Not Select')
                    )
                    entries.append(entry)
                
                self.logger.debug(f"Retrieved {len(entries)} entries for {institution_clean}")
                return entries
        except Exception as e:
            error = QueryError(message=f"Error retrieving entries for {institution}: {e}")
            self.logger.error(str(error))
            raise error from e
    
    def save_entry(self, entry: Entry) -> None:
        """
        Save an entry to the database.
        
        Args:
            entry (Entry): The entry to save
            
        Raises:
            QueryError: If entry save fails
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO entries (institution, event_number, data)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (institution, event_number) 
                    DO UPDATE SET data = EXCLUDED.data;
                """, (
                    entry.institution.lower(),
                    entry.event_number,
                    json.dumps(entry.data)
                ))
            
            self.logger.debug(f"Saved entry {entry.event_number} for {entry.institution}")
        except Exception as e:
            error = QueryError(
                message=f"Error saving entry {entry.event_number} for {entry.institution}: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    def save_entries(self, entries: List[Entry]) -> None:
        """
        Save multiple entries to the database in a batch.
        
        Args:
            entries (List[Entry]): The entries to save
            
        Raises:
            QueryError: If batch entry save fails
        """
        if not entries:
            return
            
        try:
            # Group entries by institution for better logging
            entries_by_institution = {}
            for entry in entries:
                institution = entry.institution.lower()
                if institution not in entries_by_institution:
                    entries_by_institution[institution] = []
                entries_by_institution[institution].append(entry)
            
            with self.connection.cursor() as cursor:
                insert_query = """
                    INSERT INTO entries (institution, event_number, data)
                    VALUES %s
                    ON CONFLICT (institution, event_number)
                    DO UPDATE SET data = EXCLUDED.data;
                """
                
                # Prepare values for execute_values
                values = [
                    (entry.institution.lower(), entry.event_number, json.dumps(entry.data))
                    for entry in entries
                ]
                
                # Execute batch insert
                psycopg2.extras.execute_values(
                    cursor, insert_query, values, template=None, page_size=100
                )
            
            # Log results
            for institution, inst_entries in entries_by_institution.items():
                self.logger.debug(f"Saved {len(inst_entries)} entries for {institution}")
        except Exception as e:
            error = QueryError(message=f"Error batch saving entries: {e}")
            self.logger.error(str(error))
            raise error from e
    
    def get_entry(self, institution: str, event_number: str) -> Entry:
        """
        Get a specific entry by institution and event number.
        
        Args:
            institution (str): The institution
            event_number (str): The event number
            
        Returns:
            Entry: The entry
            
        Raises:
            RecordNotFoundError: If the entry is not found
            QueryError: If query execution fails
        """
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT institution, event_number, data
                    FROM entries
                    WHERE LOWER(TRIM(institution)) = %s AND event_number = %s;
                """, (institution_clean, event_number))
                
                row = cursor.fetchone()
                if not row:
                    raise RecordNotFoundError(
                        table='entries',
                        criteria={'institution': institution_clean, 'event_number': event_number}
                    )
                
                # Convert row to Entry object
                data = row['data']
                entry = Entry(
                    institution=institution_clean,
                    event_number=row['event_number'],
                    data=data,
                    selected=data.get('Selected', 'Do Not Select')
                )
                
                return entry
        except RecordNotFoundError:
            # Re-raise record not found errors
            raise
        except Exception as e:
            error = QueryError(
                message=f"Error retrieving entry {event_number} for {institution}: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    def update_entry(self, entry: Entry) -> None:
        """
        Update an existing entry.
        
        Args:
            entry (Entry): The entry to update
            
        Raises:
            QueryError: If entry update fails
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE entries
                    SET data = %s
                    WHERE LOWER(TRIM(institution)) = %s AND event_number = %s;
                """, (
                    json.dumps(entry.data),
                    entry.institution.lower(),
                    entry.event_number
                ))
                
                if cursor.rowcount == 0:
                    # If no rows were updated, the entry doesn't exist
                    raise RecordNotFoundError(
                        table='entries',
                        criteria={'institution': entry.institution, 'event_number': entry.event_number}
                    )
            
            self.logger.debug(f"Updated entry {entry.event_number} for {entry.institution}")
        except RecordNotFoundError:
            # Re-raise record not found errors
            raise
        except Exception as e:
            error = QueryError(
                message=f"Error updating entry {entry.event_number} for {entry.institution}: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    # Evaluation operations
    
    def get_evaluation(self, institution: str, evaluator: str, entry_number: str) -> Optional[Evaluation]:
        """
        Get an evaluation by institution, evaluator, and entry number.
        
        Args:
            institution (str): The institution
            evaluator (str): The evaluator
            entry_number (str): The entry number
            
        Returns:
            Optional[Evaluation]: The evaluation or None if not found
            
        Raises:
            QueryError: If query execution fails
        """
        try:
            institution_clean = institution.strip().lower()
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT *
                    FROM evaluations
                    WHERE LOWER(TRIM(institution)) = %s 
                      AND evaluator = %s 
                      AND entry_number = %s;
                """, (institution_clean, evaluator, entry_number))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Convert row to Evaluation object
                evaluation = Evaluation(
                    institution=institution_clean,
                    evaluator=row['evaluator'],
                    entry_number=row['entry_number'],
                    summary_score=row['summary_score'],
                    tag_score=row['tag_score'],
                    feedback=row['feedback'] or ''
                )
                
                return evaluation
        except Exception as e:
            error = QueryError(
                message=f"Error retrieving evaluation for {evaluator}, entry {entry_number}: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    def save_evaluation(self, evaluation: Evaluation) -> bool:
        """
        Save an evaluation to the database.
        
        Args:
            evaluation (Evaluation): The evaluation to save
            
        Returns:
            bool: True if this was a new evaluation, False if updating existing
            
        Raises:
            QueryError: If evaluation save fails
        """
        try:
            # Check if this is a new evaluation
            is_new = self.get_evaluation(
                evaluation.institution, 
                evaluation.evaluator,
                evaluation.entry_number
            ) is None
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO evaluations 
                    (institution, evaluator, entry_number, summary_score, tag_score, feedback)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (institution, evaluator, entry_number)
                    DO UPDATE SET 
                        summary_score = EXCLUDED.summary_score,
                        tag_score = EXCLUDED.tag_score,
                        feedback = EXCLUDED.feedback;
                """, (
                    evaluation.institution.lower(),
                    evaluation.evaluator,
                    evaluation.entry_number,
                    evaluation.summary_score,
                    evaluation.tag_score,
                    evaluation.feedback
                ))
            
            self.logger.debug(
                f"{'Created new' if is_new else 'Updated'} evaluation "
                f"for {evaluation.evaluator}, entry {evaluation.entry_number}"
            )
            
            return is_new
        except Exception as e:
            error = QueryError(
                message=f"Error saving evaluation for {evaluation.evaluator}, entry {evaluation.entry_number}: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    def get_evaluations_by_evaluator(self, evaluator: str, institution: str = None) -> List[Evaluation]:
        """
        Get all evaluations by a specific evaluator.
        
        Args:
            evaluator (str): The evaluator
            institution (str, optional): Filter by institution
            
        Returns:
            List[Evaluation]: List of evaluations
            
        Raises:
            QueryError: If query execution fails
        """
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if institution:
                    institution_clean = institution.strip().lower()
                    cursor.execute("""
                        SELECT *
                        FROM evaluations
                        WHERE evaluator = %s AND LOWER(TRIM(institution)) = %s
                        ORDER BY entry_number;
                    """, (evaluator, institution_clean))
                else:
                    cursor.execute("""
                        SELECT *
                        FROM evaluations
                        WHERE evaluator = %s
                        ORDER BY institution, entry_number;
                    """, (evaluator,))
                
                rows = cursor.fetchall()
                evaluations = []
                
                for row in rows:
                    evaluation = Evaluation(
                        institution=row['institution'],
                        evaluator=row['evaluator'],
                        entry_number=row['entry_number'],
                        summary_score=row['summary_score'],
                        tag_score=row['tag_score'],
                        feedback=row['feedback'] or ''
                    )
                    evaluations.append(evaluation)
                
                return evaluations
        except Exception as e:
            error = QueryError(
                message=f"Error retrieving evaluations for evaluator {evaluator}: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    def count_evaluations_by_evaluator(self, evaluator: str, institution: str = None) -> int:
        """
        Count evaluations by a specific evaluator.
        
        Args:
            evaluator (str): The evaluator
            institution (str, optional): Filter by institution
            
        Returns:
            int: Number of evaluations
            
        Raises:
            QueryError: If query execution fails
        """
        try:
            with self.connection.cursor() as cursor:
                if institution:
                    institution_clean = institution.strip().lower()
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM evaluations
                        WHERE evaluator = %s AND LOWER(TRIM(institution)) = %s;
                    """, (evaluator, institution_clean))
                else:
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM evaluations
                        WHERE evaluator = %s;
                    """, (evaluator,))
                
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            error = QueryError(
                message=f"Error counting evaluations for evaluator {evaluator}: {e}"
            )
            self.logger.error(str(error))
            raise error from e
    
    def get_all_evaluators(self) -> List[str]:
        """
        Get a list of all evaluators who have submitted evaluations.
        
        Returns:
            List[str]: List of evaluator usernames
            
        Raises:
            QueryError: If query execution fails
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT evaluator
                    FROM evaluations
                    ORDER BY evaluator;
                """)
                
                results = cursor.fetchall()
                evaluators = [row[0] for row in results]
                
                self.logger.debug(f"Retrieved {len(evaluators)} evaluators")
                return evaluators
        except Exception as e:
            error = QueryError(message=f"Error retrieving evaluators: {e}")
            self.logger.error(str(error))
            raise error from e
    
    # Institution stats operations
    
    def get_institution_stats(self, institution: str) -> InstitutionStats:
        """
        Get statistics for an institution.
        
        Args:
            institution (str): The institution
            
        Returns:
            InstitutionStats: Institution statistics
            
        Raises:
            QueryError: If query execution fails
        """
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
                    
                    stats = InstitutionStats(
                        institution=institution_clean,
                        cumulative_summary=cumulative_summary,
                        cumulative_tag=cumulative_tag,
                        total_evaluations=total_evaluations
                    )
                else:
                    # Return default stats if none found
                    stats = InstitutionStats(institution=institution_clean)
                
                return stats
        except Exception as e:
            error = QueryError(message=f"Error retrieving stats for {institution}: {e}")
            self.logger.error(str(error))
            raise error from e
    
    def update_institution_stats(self, stats: InstitutionStats) -> None:
        """
        Update statistics for an institution.
        
        Args:
            stats (InstitutionStats): The updated statistics
            
        Raises:
            QueryError: If stats update fails
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO institution_stats 
                    (institution, cumulative_summary, cumulative_tag, total_evaluations)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (institution)
                    DO UPDATE SET 
                        cumulative_summary = EXCLUDED.cumulative_summary,
                        cumulative_tag = EXCLUDED.cumulative_tag,
                        total_evaluations = EXCLUDED.total_evaluations;
                """, (
                    stats.institution.lower(),
                    stats.cumulative_summary,
                    stats.cumulative_tag,
                    stats.total_evaluations
                ))
            
            self.logger.debug(f"Updated stats for {stats.institution}")
        except Exception as e:
            error = QueryError(message=f"Error updating stats for {stats.institution}: {e}")
            self.logger.error(str(error))
            raise error from e
    
    def add_evaluation_to_stats(self, institution: str, summary_score: float, 
                              tag_score: float, is_new: bool = True,
                              old_summary: float = 0, old_tag: float = 0) -> None:
        """
        Add an evaluation to institution statistics.
        
        Args:
            institution (str): The institution
            summary_score (float): The summary score
            tag_score (float): The tag score
            is_new (bool): Whether this is a new evaluation or an update
            old_summary (float): The old summary score (for updates)
            old_tag (float): The old tag score (for updates)
            
        Raises:
            QueryError: If stats update fails
        """
        try:
            institution_clean = institution.strip().lower()
            
            # Get current stats
            stats = self.get_institution_stats(institution_clean)
            
            if is_new:
                # Add new evaluation
                stats.add_evaluation(summary_score, tag_score)
            else:
                # Update existing evaluation
                stats.update_evaluation(old_summary, summary_score, old_tag, tag_score)
            
            # Save updated stats
            self.update_institution_stats(stats)
            
        except Exception as e:
            error = QueryError(message=f"Error updating stats for {institution}: {e}")
            self.logger.error(str(error))
            raise error from e
    
    def get_evaluator_stats(self, evaluator: str, institution: str = None) -> Dict[str, Any]:
        """
        Get statistics for an evaluator.
        
        Args:
            evaluator (str): The evaluator
            institution (str, optional): Filter by institution
            
        Returns:
            Dict[str, Any]: Evaluator statistics
            
        Raises:
            QueryError: If query execution fails
        """
        try:
            with self.connection.cursor() as cursor:
                if institution:
                    institution_clean = institution.strip().lower()
                    cursor.execute("""
                        SELECT COUNT(*), AVG(summary_score), AVG(tag_score)
                        FROM evaluations
                        WHERE evaluator = %s AND LOWER(TRIM(institution)) = %s;
                    """, (evaluator, institution_clean))
                else:
                    cursor.execute("""
                        SELECT COUNT(*), AVG(summary_score), AVG(tag_score)
                        FROM evaluations
                        WHERE evaluator = %s;
                    """, (evaluator,))
                
                result = cursor.fetchone()
                if result:
                    total_evaluations, avg_summary, avg_tag = result
                    
                    return {
                        'total_evaluations': total_evaluations or 0,
                        'average_summary_score': avg_summary or 0,
                        'average_tag_score': avg_tag or 0
                    }
                else:
                    return {
                        'total_evaluations': 0,
                        'average_summary_score': 0,
                        'average_tag_score': 0
                    }
        except Exception as e:
            error = QueryError(message=f"Error retrieving stats for evaluator {evaluator}: {e}")
            self.logger.error(str(error))
            raise error from e