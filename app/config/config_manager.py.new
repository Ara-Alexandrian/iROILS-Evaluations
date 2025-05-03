"""
Configuration management system for the iROILS Evaluations application.

This module provides a singleton ConfigManager class for loading and accessing
application configuration from config.ini files.
"""

import os
import configparser
import logging
from typing import Dict, Any, Optional, Union, cast

from app.exceptions.config_exceptions import (
    ConfigFileNotFoundError,
    ConfigParsingError,
    ConfigKeyError,
    EnvironmentNotFoundError
)

class ConfigManager:
    """
    Singleton class for managing application configuration.
    
    This class implements the Singleton pattern to ensure only one configuration
    manager exists throughout the application. It handles loading configuration
    from files, providing default values, and accessing configuration settings
    based on the execution environment (home/work).
    """
    
    _instance = None
    
    def __new__(cls) -> 'ConfigManager':
        """Ensure only one instance of ConfigManager exists."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cast(ConfigManager, cls._instance)
    
    def __init__(self) -> None:
        """Initialize the configuration manager if not already initialized."""
        if getattr(self, '_initialized', False):
            return
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration parser
        self._config = configparser.ConfigParser()
        
        # Load configuration
        self._load_config()
        
        # Mark as initialized
        self._initialized = True
    
    def _get_config_path(self) -> str:
        """
        Get the path to the configuration file.
        
        Returns:
            str: Absolute path to the configuration file
        """
        # Try to locate configuration in several places
        potential_paths = [
            # Current directory
            os.path.join(os.getcwd(), 'config.ini'),
            
            # App directory
            os.path.join(os.path.dirname(__file__), '..', 'config.ini'),
            
            # Project root
            os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini'),
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                self.logger.debug(f"Found configuration file at {path}")
                return path
        
        # If we didn't find a config file, use the default location for creation
        default_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        self.logger.warning(f"No configuration file found, will create at {default_path}")
        return default_path
    
    def _load_config(self) -> None:
        """
        Load configuration from the config.ini file.
        
        Raises:
            ConfigFileNotFoundError: If the configuration file cannot be found
            ConfigParsingError: If there's an error parsing the configuration file
        """
        try:
            config_path = self._get_config_path()
            
            if not os.path.exists(config_path):
                self._create_default_config(config_path)
            
            self._config.read(config_path)
            self.logger.info(f"Configuration loaded successfully from {config_path}")
            
        except FileNotFoundError as e:
            error = ConfigFileNotFoundError(config_path)
            self.logger.error(str(error))
            raise error from e
            
        except configparser.Error as e:
            error = ConfigParsingError(config_path, e)
            self.logger.error(str(error))
            raise error from e
            
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {e}")
            raise
    
    def _create_default_config(self, config_path: str) -> None:
        """
        Create a default configuration file if it doesn't exist.
        
        Args:
            config_path (str): Path where the default configuration will be created
        """
        self.logger.info(f"Creating default configuration at {config_path}")
        
        default_config = {
            'postgresql': {
                'psql_home': '192.168.1.166',
                'psql_work': '172.30.98.x',
                'psql_port': '5432',
                'psql_user': 'aalexandrian',
                'psql_password': '1232',
                'psql_dbname': 'iroils'
            },
            'API': {
                'endpoint_home': 'http://192.168.1.5:11434/api/generate',
                'endpoint_work': 'http://172.30.98.11:11434/api/generate'
            },
            'Redis': {
                'host_home': '192.168.1.4',
                'host_work': '172.30.98.46',
                'redis_port': '6379'
            },
            'Logging': {
                'level': 'INFO',
                'file': '',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'Application': {
                'session_timeout': '900',  # 15 minutes in seconds
                'default_institution': 'UAB'
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        self._config.read_dict(default_config)
        
        with open(config_path, 'w') as configfile:
            self._config.write(configfile)
        
        self.logger.info(f"Default configuration created at {config_path}")
    
    def get_postgresql_config(self, environment: str = 'home') -> Dict[str, Any]:
        """
        Get PostgreSQL configuration for the specified environment.
        
        Args:
            environment (str): The environment to get configuration for ('home' or 'work')
            
        Returns:
            Dict[str, Any]: Dictionary containing PostgreSQL connection parameters
            
        Raises:
            ConfigKeyError: If a required configuration key is missing
            EnvironmentNotFoundError: If the specified environment is not found
        """
        try:
            # Validate environment
            if environment not in ['home', 'work']:
                raise EnvironmentNotFoundError(environment)
            
            return {
                'host': self._config['postgresql'][f'psql_{environment}'],
                'port': self._config['postgresql'].getint('psql_port', 5432),
                'user': self._config['postgresql']['psql_user'],
                'password': self._config['postgresql']['psql_password'],
                'dbname': self._config['postgresql']['psql_dbname']
            }
        except KeyError as e:
            error = ConfigKeyError('postgresql', str(e))
            self.logger.error(str(error))
            raise error from e
    
    def get_api_config(self, environment: str = 'home') -> str:
        """
        Get API endpoint configuration for the specified environment.
        
        Args:
            environment (str): The environment to get configuration for ('home' or 'work')
            
        Returns:
            str: API endpoint URL
            
        Raises:
            ConfigKeyError: If a required configuration key is missing
            EnvironmentNotFoundError: If the specified environment is not found
        """
        try:
            # Validate environment
            if environment not in ['home', 'work']:
                raise EnvironmentNotFoundError(environment)
                
            return self._config['API'][f'endpoint_{environment}']
        except KeyError as e:
            error = ConfigKeyError('API', str(e))
            self.logger.error(str(error))
            raise error from e
    
    def get_redis_config(self, environment: str = 'home') -> Dict[str, Any]:
        """
        Get Redis configuration for the specified environment.
        
        Args:
            environment (str): The environment to get configuration for ('home' or 'work')
            
        Returns:
            Dict[str, Any]: Dictionary containing Redis connection parameters
            
        Raises:
            ConfigKeyError: If a required configuration key is missing
            EnvironmentNotFoundError: If the specified environment is not found
        """
        try:
            # Validate environment
            if environment not in ['home', 'work']:
                raise EnvironmentNotFoundError(environment)
                
            return {
                'host': self._config['Redis'][f'host_{environment}'],
                'port': self._config['Redis'].getint('redis_port', 6379)
            }
        except KeyError as e:
            error = ConfigKeyError('Redis', str(e))
            self.logger.error(str(error))
            raise error from e
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Dict[str, Any]: Dictionary containing logging configuration
        """
        return {
            'level': self._config.get('Logging', 'level', fallback='INFO'),
            'file': self._config.get('Logging', 'file', fallback=''),
            'format': self._config.get('Logging', 'format', 
                                      fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        }
    
    def get_application_config(self) -> Dict[str, Any]:
        """
        Get general application configuration.
        
        Returns:
            Dict[str, Any]: Dictionary containing application configuration
        """
        return {
            'session_timeout': self._config.getint('Application', 'session_timeout', fallback=900),
            'default_institution': self._config.get('Application', 'default_institution', fallback='UAB')
        }
    
    def get_value(self, section: str, key: str, fallback: Optional[Any] = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (Any, optional): Default value if the key is not found
            
        Returns:
            Any: Configuration value
            
        Raises:
            ConfigKeyError: If the key is not found and no fallback is provided
        """
        try:
            return self._config[section][key]
        except KeyError:
            if fallback is not None:
                return fallback
            
            error = ConfigKeyError(section, key)
            self.logger.error(str(error))
            raise error
    
    def get_int(self, section: str, key: str, fallback: Optional[int] = None) -> int:
        """
        Get a specific configuration value as an integer.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (int, optional): Default value if the key is not found
            
        Returns:
            int: Configuration value as an integer
            
        Raises:
            ConfigKeyError: If the key is not found and no fallback is provided
            ValueError: If the value cannot be converted to an integer
        """
        try:
            return self._config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            
            error = ConfigKeyError(section, key)
            self.logger.error(str(error))
            raise error
        except ValueError as e:
            self.logger.error(f"Value for [{section}]{key} is not a valid integer")
            raise ValueError(f"Value for [{section}]{key} is not a valid integer") from e
    
    def get_float(self, section: str, key: str, fallback: Optional[float] = None) -> float:
        """
        Get a specific configuration value as a float.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (float, optional): Default value if the key is not found
            
        Returns:
            float: Configuration value as a float
            
        Raises:
            ConfigKeyError: If the key is not found and no fallback is provided
            ValueError: If the value cannot be converted to a float
        """
        try:
            return self._config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            
            error = ConfigKeyError(section, key)
            self.logger.error(str(error))
            raise error
        except ValueError as e:
            self.logger.error(f"Value for [{section}]{key} is not a valid float")
            raise ValueError(f"Value for [{section}]{key} is not a valid float") from e
    
    def get_boolean(self, section: str, key: str, fallback: Optional[bool] = None) -> bool:
        """
        Get a specific configuration value as a boolean.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            fallback (bool, optional): Default value if the key is not found
            
        Returns:
            bool: Configuration value as a boolean
            
        Raises:
            ConfigKeyError: If the key is not found and no fallback is provided
            ValueError: If the value cannot be converted to a boolean
        """
        try:
            return self._config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            
            error = ConfigKeyError(section, key)
            self.logger.error(str(error))
            raise error
        except ValueError as e:
            self.logger.error(f"Value for [{section}]{key} is not a valid boolean")
            raise ValueError(f"Value for [{section}]{key} is not a valid boolean") from e