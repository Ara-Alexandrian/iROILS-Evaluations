"""
Network utility functions and classes for the iROILS Evaluations application.

This module provides utilities for network-related operations such as 
detecting the local IP address and determining the execution environment.
"""

import socket
import logging
from typing import Literal, Dict

from app.exceptions.config_exceptions import EnvironmentNotFoundError

# Define environment type
EnvironmentType = Literal['home', 'work']

class NetworkResolver:
    """
    Utility class for network operations and environment detection.
    
    This class provides methods for determining the local IP address and
    resolving the execution environment (home or work network).
    """
    
    def __init__(self, config: 'ConfigManager') -> None:
        """
        Initialize the NetworkResolver.
        
        Args:
            config: The application configuration manager
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Define network prefixes for environment detection
        self.environment_prefixes: Dict[str, EnvironmentType] = {
            '192.168.1.': 'home',
            '172.30.98.': 'work'
        }
    
    def get_local_ip(self) -> str:
        """
        Get the local IP address of the machine.
        
        Returns:
            str: The local IP address
            
        Raises:
            ConnectionError: If unable to determine local IP address
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Connect to an external server to determine local IP
            # Note: No actual connection is made, just a socket setup
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
            self.logger.info(f"Local IP detected: {local_ip}")
            return local_ip
        except Exception as e:
            error_msg = f"Failed to determine local IP: {e}"
            self.logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        finally:
            s.close()
    
    def resolve_environment(self, local_ip: str) -> EnvironmentType:
        """
        Determine the environment based on the local IP address.
        
        Args:
            local_ip (str): The local IP address to check
            
        Returns:
            EnvironmentType: The determined environment ('home' or 'work')
        """
        # Check if IP matches any known environment prefix
        for prefix, environment in self.environment_prefixes.items():
            if local_ip.startswith(prefix):
                self.logger.info(f"Detected {environment} network from IP {local_ip}")
                return environment
        
        # Default to 'home' if subnet is unknown
        self.logger.warning(f"Unknown subnet {local_ip}. Defaulting to 'home' environment.")
        return 'home'
    
    def get_environment(self) -> EnvironmentType:
        """
        Get the current execution environment.
        
        This is a convenience method that calls get_local_ip and resolve_environment.
        
        Returns:
            EnvironmentType: The determined environment ('home' or 'work')
        """
        local_ip = self.get_local_ip()
        return self.resolve_environment(local_ip)
    
    def get_connection_params(self, service_type: str) -> Dict[str, str]:
        """
        Get connection parameters for a service based on the current environment.
        
        Args:
            service_type (str): The type of service ('postgresql', 'redis', 'api')
            
        Returns:
            Dict[str, str]: Connection parameters for the service
            
        Raises:
            EnvironmentNotFoundError: If the environment cannot be determined
            ValueError: If the service type is not supported
        """
        # Get current environment
        environment = self.get_environment()
        
        # Return connection parameters based on service type
        if service_type.lower() == 'postgresql':
            return self.config.get_postgresql_config(environment)
        elif service_type.lower() == 'redis':
            return self.config.get_redis_config(environment)
        elif service_type.lower() == 'api':
            return {'endpoint': self.config.get_api_config(environment)}
        else:
            raise ValueError(f"Unsupported service type: {service_type}")