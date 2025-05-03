"""
User models for the iROILS Evaluations application.
"""

from typing import Dict, List, Optional, Literal, Union
from dataclasses import dataclass

# Define user role type
UserRole = Literal['admin', 'evaluator']

@dataclass
class User:
    """Base user model with common attributes."""
    username: str
    role: UserRole
    
    def has_role(self, role: UserRole) -> bool:
        """
        Check if the user has the specified role.
        
        Args:
            role (UserRole): The role to check
            
        Returns:
            bool: True if the user has the role, False otherwise
        """
        return self.role == role


@dataclass
class AdminUser(User):
    """Admin user model with admin-specific attributes."""
    
    def __init__(self, username: str):
        """
        Initialize an admin user.
        
        Args:
            username (str): The admin's username
        """
        super().__init__(username=username, role='admin')


@dataclass
class EvaluatorUser(User):
    """Evaluator user model with evaluator-specific attributes."""
    institution: str
    
    def __init__(self, username: str, institution: str):
        """
        Initialize an evaluator user.
        
        Args:
            username (str): The evaluator's username
            institution (str): The evaluator's institution
        """
        super().__init__(username=username, role='evaluator')
        self.institution = institution