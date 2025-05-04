"""
Session management for the iROILS Evaluations application.

This module provides utilities for managing user sessions and state.
"""

import logging
from typing import Dict, Any, Optional, TypeVar, Generic, Callable, cast

T = TypeVar('T')

class SessionState(Generic[T]):
    """
    Generic session state accessor for Streamlit sessions.
    
    This class provides type-safe access to session state variables,
    with support for default values and type checking.
    """
    
    def __init__(self, session_state: Dict[str, Any]):
        """
        Initialize the session state accessor.
        
        Args:
            session_state (Dict[str, Any]): The session state dictionary
        """
        self.session_state = session_state
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get a value from the session state with an optional default.
        
        Args:
            key (str): The session state key
            default (Optional[T]): The default value to return if the key is not found
            
        Returns:
            Optional[T]: The session state value or the default
        """
        return cast(Optional[T], self.session_state.get(key, default))
    
    def set(self, key: str, value: T) -> None:
        """
        Set a value in the session state.
        
        Args:
            key (str): The session state key
            value (T): The value to set
        """
        self.session_state[key] = value
    
    def pop(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Remove a value from the session state and return it.
        
        Args:
            key (str): The session state key
            default (Optional[T]): The default value to return if the key is not found
            
        Returns:
            Optional[T]: The removed session state value or the default
        """
        return cast(Optional[T], self.session_state.pop(key, default))
    
    def clear(self, prefix: Optional[str] = None) -> None:
        """
        Clear all or prefixed variables from the session state.
        
        Args:
            prefix (Optional[str]): If provided, only clear variables starting with this prefix
        """
        if prefix:
            # Create a list of keys to remove (can't modify during iteration)
            keys_to_remove = [key for key in self.session_state if key.startswith(prefix)]
            for key in keys_to_remove:
                self.session_state.pop(key, None)
            self.logger.debug(f"Cleared {len(keys_to_remove)} items with prefix '{prefix}' from session state")
        else:
            # Clear all items
            self.session_state.clear()
            self.logger.debug("Cleared all items from session state")
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in the session state.
        
        Args:
            key (str): The session state key
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        return key in self.session_state
    
    def require(self, key: str) -> T:
        """
        Get a required value from the session state.
        
        Args:
            key (str): The session state key
            
        Returns:
            T: The session state value
            
        Raises:
            KeyError: If the key is not found in the session state
        """
        if key not in self.session_state:
            raise KeyError(f"Required session state key not found: {key}")
        
        return cast(T, self.session_state[key])
    
    def transform(self, key: str, transformer: Callable[[T], T], default: Optional[T] = None) -> T:
        """
        Transform a value in the session state.
        
        Args:
            key (str): The session state key
            transformer (Callable[[T], T]): Function to transform the value
            default (Optional[T]): Default value if the key doesn't exist
            
        Returns:
            T: The transformed value
        """
        value = self.get(key, default)
        transformed = transformer(value) if value is not None else None
        
        if transformed is not None:
            self.set(key, transformed)
            
        return cast(T, transformed)


def get_session_state(st_session_state: Dict[str, Any]) -> SessionState:
    """
    Create a SessionState wrapper for a Streamlit session state.
    
    Args:
        st_session_state (Dict[str, Any]): The Streamlit session state
        
    Returns:
        SessionState: A SessionState wrapper for the Streamlit session state
    """
    return SessionState(st_session_state)