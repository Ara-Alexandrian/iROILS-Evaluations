"""Unit tests for the ConfigManager class."""

import os
import pytest
from unittest.mock import patch, mock_open

from app.exceptions.config_exceptions import ConfigKeyError, EnvironmentNotFoundError
from app.config.config_manager import ConfigManager


class TestConfigManager:
    """Tests for the ConfigManager class."""

    def test_singleton_pattern(self):
        """Test that ConfigManager implements the singleton pattern."""
        # Create two instances
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        # Verify they are the same object
        assert config1 is config2
    
    @patch('os.path.exists')
    @patch('configparser.ConfigParser.read')
    def test_load_config(self, mock_read, mock_exists):
        """Test loading configuration from file."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Create ConfigManager instance
        config = ConfigManager()
        
        # Verify config file was read
        mock_read.assert_called_once()
    
    @patch('os.path.exists')
    @patch('configparser.ConfigParser.read')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_default_config(self, mock_file, mock_read, mock_exists):
        """Test creating default configuration."""
        # Mock file does not exist
        mock_exists.return_value = False
        
        # Create ConfigManager instance
        config = ConfigManager()
        
        # Verify default config was created
        mock_file.assert_called_once()
    
    @patch('os.path.exists')
    @patch('configparser.ConfigParser.read')
    def test_get_postgresql_config(self, mock_read, mock_exists):
        """Test getting PostgreSQL configuration."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Create ConfigManager instance with mocked config
        config = ConfigManager()
        config._config = {
            'postgresql': {
                'psql_home': 'localhost',
                'psql_work': 'workserver',
                'psql_port': '5432',
                'psql_user': 'user',
                'psql_password': 'password',
                'psql_dbname': 'dbname'
            }
        }
        config._config.getint = lambda section, key, fallback=None: int(config._config[section][key])
        
        # Test home environment
        result = config.get_postgresql_config('home')
        assert result['host'] == 'localhost'
        assert result['port'] == 5432
        
        # Test work environment
        result = config.get_postgresql_config('work')
        assert result['host'] == 'workserver'
        
        # Test invalid environment
        with pytest.raises(EnvironmentNotFoundError):
            config.get_postgresql_config('invalid')
    
    @patch('os.path.exists')
    @patch('configparser.ConfigParser.read')
    def test_get_value(self, mock_read, mock_exists):
        """Test getting a specific configuration value."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Create ConfigManager instance with mocked config
        config = ConfigManager()
        config._config = {
            'section1': {
                'key1': 'value1',
                'key2': 'value2'
            }
        }
        
        # Test get existing value
        assert config.get_value('section1', 'key1') == 'value1'
        
        # Test get value with fallback
        assert config.get_value('section1', 'nonexistent', 'default') == 'default'
        
        # Test get value without fallback
        with pytest.raises(ConfigKeyError):
            config.get_value('section1', 'nonexistent')