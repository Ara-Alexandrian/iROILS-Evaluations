"""
Configuration management for the iROILS Evaluations application.
"""

from app.config.config_manager import ConfigManager

# Singleton instance to be used throughout the application
config = ConfigManager()

__all__ = ['config', 'ConfigManager']