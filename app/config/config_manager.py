# app/config/config_manager.py

import os
import configparser
import logging
from typing import Dict, Any

class ConfigManager:
  _instance = None
  
  def __new__(cls):
      if cls._instance is None:
          cls._instance = super(ConfigManager, cls).__new__(cls)
          cls._instance._initialized = False
      return cls._instance

  def __init__(self):
      if self._initialized:
          return
          
      self.logger = logging.getLogger(__name__)
      self._config = configparser.ConfigParser()
      self._load_config()
      self._initialized = True

  def _load_config(self):
      """Load configuration from config.ini file"""
      try:
          config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
          if not os.path.exists(config_path):
              self._create_default_config(config_path)
          
          self._config.read(config_path)
          self.logger.info("Configuration loaded successfully")
      except Exception as e:
          self.logger.error(f"Error loading configuration: {e}")
          raise

  def _create_default_config(self, config_path: str):
      """Create default configuration file if it doesn't exist"""
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
          }
      }

      self._config.read_dict(default_config)
      with open(config_path, 'w') as configfile:
          self._config.write(configfile)

  def get_postgresql_config(self, environment: str = 'home') -> Dict[str, Any]:
      """Get PostgreSQL configuration for specified environment"""
      try:
          return {
              'host': self._config['postgresql'][f'psql_{environment}'],
              'port': self._config['postgresql'].getint('psql_port', 5432),
              'user': self._config['postgresql']['psql_user'],
              'password': self._config['postgresql']['psql_password'],
              'dbname': self._config['postgresql']['psql_dbname']
          }
      except KeyError as e:
          self.logger.error(f"Missing PostgreSQL configuration key: {e}")
          raise

  def get_api_config(self, environment: str = 'home') -> str:
      """Get API endpoint for specified environment"""
      try:
          return self._config['API'][f'endpoint_{environment}']
      except KeyError as e:
          self.logger.error(f"Missing API configuration key: {e}")
          raise

  def get_redis_config(self, environment: str = 'home') -> Dict[str, Any]:
      """Get Redis configuration for specified environment"""
      try:
          return {
              'host': self._config['Redis'][f'host_{environment}'],
              'port': self._config['Redis'].getint('redis_port', 6379)
          }
      except KeyError as e:
          self.logger.error(f"Missing Redis configuration key: {e}")
          raise

  def get_value(self, section: str, key: str, fallback: Any = None) -> Any:
      """Get a specific configuration value"""
      try:
          return self._config[section][key]
      except KeyError:
          if fallback is not None:
              return fallback
          self.logger.error(f"Missing configuration key: [{section}]{key}")
          raise