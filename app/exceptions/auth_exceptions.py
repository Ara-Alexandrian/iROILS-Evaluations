"""
Authentication-related exception classes.
"""

class AuthError(Exception):
    """Base class for authentication errors."""
    pass


class InvalidCredentialsError(AuthError):
    """Exception raised when login credentials are invalid."""
    def __init__(self, username=None, message=None):
        self.username = username
        self.message = message or f"Invalid credentials for user: {username}" if username else "Invalid credentials"
        super().__init__(self.message)


class SessionExpiredError(AuthError):
    """Exception raised when a user session has expired."""
    def __init__(self, message=None):
        self.message = message or "User session has expired"
        super().__init__(self.message)


class UnauthorizedAccessError(AuthError):
    """Exception raised when a user attempts to access a resource they are not authorized for."""
    def __init__(self, username=None, resource=None, message=None):
        self.username = username
        self.resource = resource
        
        if message:
            self.message = message
        elif username and resource:
            self.message = f"User {username} is not authorized to access {resource}"
        elif username:
            self.message = f"User {username} is not authorized for this operation"
        elif resource:
            self.message = f"Unauthorized access to {resource}"
        else:
            self.message = "Unauthorized access"
            
        super().__init__(self.message)


class InsufficientPermissionsError(AuthError):
    """Exception raised when a user has insufficient permissions for an operation."""
    def __init__(self, username=None, required_role=None, message=None):
        self.username = username
        self.required_role = required_role
        
        if message:
            self.message = message
        elif username and required_role:
            self.message = f"User {username} has insufficient permissions (requires {required_role})"
        elif required_role:
            self.message = f"Insufficient permissions (requires {required_role})"
        else:
            self.message = "Insufficient permissions for this operation"
            
        super().__init__(self.message)