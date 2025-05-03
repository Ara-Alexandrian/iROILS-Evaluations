"""
Evaluation model for the iROILS Evaluations application.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Evaluation:
    """
    Model representing an evaluation of an entry.
    
    An evaluation is created by an evaluator for a specific entry,
    and includes summary and tag scores along with feedback.
    """
    
    # Core attributes
    institution: str
    evaluator: str
    entry_number: str
    summary_score: int
    tag_score: int
    feedback: str = ''
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'Evaluation':
        """
        Create an Evaluation object from a dictionary.
        
        Args:
            data_dict (Dict[str, Any]): Dictionary containing evaluation data
            
        Returns:
            Evaluation: The created Evaluation object
        """
        return cls(
            institution=data_dict.get('institution', '').lower().strip(),
            evaluator=data_dict.get('evaluator', ''),
            entry_number=str(data_dict.get('entry_number', '')),
            summary_score=int(data_dict.get('summary_score', 0)),
            tag_score=int(data_dict.get('tag_score', 0)),
            feedback=data_dict.get('feedback', '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Evaluation object to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the Evaluation
        """
        return {
            'institution': self.institution,
            'evaluator': self.evaluator,
            'entry_number': self.entry_number,
            'summary_score': self.summary_score,
            'tag_score': self.tag_score,
            'feedback': self.feedback
        }