"""
Database-related exception classes.
"""

class DatabaseError(Exception):
    """Base class for database errors."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when a database connection fails."""
    def __init__(self, host=None, port=None, db_name=None, message=None):
        self.host = host
        self.port = port
        self.db_name = db_name
        
        if message:
            self.message = message
        elif host and port and db_name:
            self.message = f"Failed to connect to database {db_name} at {host}:{port}"
        elif host and port:
            self.message = f"Failed to connect to database at {host}:{port}"
        elif host:
            self.message = f"Failed to connect to database at {host}"
        else:
            self.message = "Failed to connect to database"
            
        super().__init__(self.message)


class QueryError(DatabaseError):
    """Exception raised when a database query fails."""
    def __init__(self, query=None, params=None, original_error=None, message=None):
        self.query = query
        self.params = params
        self.original_error = original_error
        
        if message:
            self.message = message
        elif query and original_error:
            self.message = f"Query failed: {original_error}"
        elif original_error:
            self.message = f"Database operation failed: {original_error}"
        else:
            self.message = "Database query failed"
            
        super().__init__(self.message)


class IntegrityError(DatabaseError):
    """Exception raised when a database integrity constraint is violated."""
    def __init__(self, constraint=None, original_error=None, message=None):
        self.constraint = constraint
        self.original_error = original_error
        
        if message:
            self.message = message
        elif constraint and original_error:
            self.message = f"Integrity constraint violation on {constraint}: {original_error}"
        elif constraint:
            self.message = f"Integrity constraint violation on {constraint}"
        elif original_error:
            self.message = f"Integrity constraint violation: {original_error}"
        else:
            self.message = "Integrity constraint violation"
            
        super().__init__(self.message)


class RecordNotFoundError(DatabaseError):
    """Exception raised when a database record is not found."""
    def __init__(self, table=None, criteria=None, message=None):
        self.table = table
        self.criteria = criteria
        
        if message:
            self.message = message
        elif table and criteria:
            criteria_str = ", ".join(f"{k}={v}" for k, v in criteria.items())
            self.message = f"Record not found in {table} with criteria: {criteria_str}"
        elif table:
            self.message = f"Record not found in {table}"
        else:
            self.message = "Record not found"
            
        super().__init__(self.message)