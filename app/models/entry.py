"""
Entry model for the iROILS Evaluations application.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Entry:
    """
    Model representing an evaluation entry.
    
    An entry is a record that can be evaluated by users.
    It contains a unique event number within an institution context,
    and arbitrary data represented as a dictionary.
    """
    
    # Core attributes
    institution: str
    event_number: str
    data: Dict[str, Any]
    
    # Selection status (defaults to 'Do Not Select')
    selected: str = 'Do Not Select'
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'Entry':
        """
        Create an Entry object from a dictionary.
        
        Args:
            data_dict (Dict[str, Any]): Dictionary containing entry data
            
        Returns:
            Entry: The created Entry object
        """
        # Extract core fields
        institution = data_dict.get('institution', '').lower().strip()
        event_number = str(data_dict.get('Event Number', ''))
        
        # Extract selection status
        selected = data_dict.get('Selected', 'Do Not Select')
        
        # Create a copy of the data dict without the institution field
        # (institution is already a property of the Entry)
        entry_data = {k: v for k, v in data_dict.items() if k != 'institution'}
        
        return cls(
            institution=institution,
            event_number=event_number,
            data=entry_data,
            selected=selected
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Entry object to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the Entry
        """
        # Start with the data dictionary
        result = self.data.copy()
        
        # Add/override core fields
        result['institution'] = self.institution
        result['Event Number'] = self.event_number
        result['Selected'] = self.selected
        
        return result
    
    def update_selection_status(self, status: str) -> None:
        """
        Update the selection status of the entry.
        
        Args:
            status (str): The new selection status
        """
        self.selected = status
        if 'Selected' in self.data:
            self.data['Selected'] = status
        else:
            self.data['Selected'] = status
    
    @property
    def is_selected(self) -> bool:
        """
        Check if the entry is selected for evaluation.
        
        Returns:
            bool: True if the entry is selected, False otherwise
        """
        return self.selected != 'Do Not Select'