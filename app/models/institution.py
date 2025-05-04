"""
Institution model for the iROILS Evaluations application.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class InstitutionStats:
    """
    Model representing institution statistics.
    
    This class stores aggregated statistics for an institution,
    including cumulative scores and total evaluations.
    """
    
    institution: str
    cumulative_summary: float = 0.0
    cumulative_tag: float = 0.0
    total_evaluations: int = 0
    
    @property
    def average_summary(self) -> float:
        """
        Calculate the average summary score.
        
        Returns:
            float: Average summary score, or 0 if no evaluations
        """
        if self.total_evaluations > 0:
            return self.cumulative_summary / self.total_evaluations
        return 0.0
    
    @property
    def average_tag(self) -> float:
        """
        Calculate the average tag score.
        
        Returns:
            float: Average tag score, or 0 if no evaluations
        """
        if self.total_evaluations > 0:
            return self.cumulative_tag / self.total_evaluations
        return 0.0
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'InstitutionStats':
        """
        Create an InstitutionStats object from a dictionary.
        
        Args:
            data_dict (Dict[str, Any]): Dictionary containing institution stats
            
        Returns:
            InstitutionStats: The created InstitutionStats object
        """
        return cls(
            institution=data_dict.get('institution', '').lower().strip(),
            cumulative_summary=float(data_dict.get('cumulative_summary', 0.0)),
            cumulative_tag=float(data_dict.get('cumulative_tag', 0.0)),
            total_evaluations=int(data_dict.get('total_evaluations', 0))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the InstitutionStats object to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the InstitutionStats
        """
        return {
            'institution': self.institution,
            'cumulative_summary': self.cumulative_summary,
            'cumulative_tag': self.cumulative_tag,
            'total_evaluations': self.total_evaluations,
            'average_summary': self.average_summary,
            'average_tag': self.average_tag
        }
    
    def add_evaluation(self, summary_score: float, tag_score: float) -> None:
        """
        Add a new evaluation to the institution statistics.
        
        Args:
            summary_score (float): The summary score to add
            tag_score (float): The tag score to add
        """
        self.cumulative_summary += float(summary_score)
        self.cumulative_tag += float(tag_score)
        self.total_evaluations += 1
    
    def update_evaluation(self, old_summary: float, new_summary: float, 
                         old_tag: float, new_tag: float) -> None:
        """
        Update an existing evaluation in the institution statistics.
        
        Args:
            old_summary (float): The old summary score to replace
            new_summary (float): The new summary score
            old_tag (float): The old tag score to replace
            new_tag (float): The new tag score
        """
        self.cumulative_summary += (float(new_summary) - float(old_summary))
        self.cumulative_tag += (float(new_tag) - float(old_tag))