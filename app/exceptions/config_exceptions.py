"""
Configuration-related exception classes.
"""

class ConfigError(Exception):
    """Base class for configuration errors."""
    pass


class ConfigFileNotFoundError(ConfigError):
    """Exception raised when the configuration file is not found."""
    def __init__(self, file_path, message=None):
        self.file_path = file_path
        self.message = message or f"Configuration file not found: {file_path}"
        super().__init__(self.message)


class ConfigParsingError(ConfigError):
    """Exception raised when there's an error parsing the configuration file."""
    def __init__(self, file_path, original_error, message=None):
        self.file_path = file_path
        self.original_error = original_error
        self.message = message or f"Error parsing configuration file {file_path}: {original_error}"
        super().__init__(self.message)


class ConfigKeyError(ConfigError):
    """Exception raised when a required configuration key is missing."""
    def __init__(self, section, key, message=None):
        self.section = section
        self.key = key
        self.message = message or f"Missing required configuration key: [{section}] {key}"
        super().__init__(self.message)


class EnvironmentNotFoundError(ConfigError):
    """Exception raised when the specified environment is not found in the configuration."""
    def __init__(self, environment, message=None):
        self.environment = environment
        self.message = message or f"Environment not found in configuration: {environment}"
        super().__init__(self.message)