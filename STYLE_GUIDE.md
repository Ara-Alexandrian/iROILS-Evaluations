# iROILS Evaluations Style Guide

This document outlines the coding style and conventions to follow when working on the iROILS Evaluations project.

## Python Code Style

### Naming Conventions

1. **Classes**: Use `CamelCase` for class names
   - Example: `DatabaseManager`, `LoginManager`

2. **Functions and Methods**: Use `snake_case` for function and method names
   - Example: `get_evaluation`, `update_entry`

3. **Variables**: Use `snake_case` for variable names
   - Example: `user_name`, `entry_number`

4. **Constants**: Use `UPPER_CASE` with underscores
   - Example: `DEFAULT_PORT`, `SESSION_TIMEOUT`

5. **Module Names**: Use `snake_case` for module names
   - Example: `database_manager.py`, `login_manager.py`

6. **Package Names**: Use `snake_case` for package names
   - Example: `utils`, `pages`

### Code Structure

1. **Imports**:
   - Group imports in the following order:
     1. Standard library imports
     2. Third-party library imports
     3. Application-specific imports
   - Sort imports alphabetically within each group
   - Separate each group with a blank line

2. **Class Structure**:
   - Order class methods as follows:
     1. `__init__` and other special methods
     2. Class methods
     3. Static methods
     4. Public methods
     5. Private methods (prefixed with `_`)

3. **Function Documentation**:
   - Use docstrings for all functions and methods
   - Follow Google-style docstrings
   - Include type hints for function parameters and return values

### Code Styling

1. **Line Length**: Maximum line length of 100 characters
2. **Indentation**: 4 spaces (no tabs)
3. **String Quotes**: Use single quotes for strings, double quotes for docstrings
4. **Whitespace**:
   - No trailing whitespace
   - Add blank lines between functions and classes
   - Add a blank line at the end of each file

## Project Structure

### Directory Organization

1. **Main Application**:
   - Place core application code in the `app` directory
   - Organize related functionality into subdirectories

2. **Configuration**:
   - Store all configuration-related code in the `app/config` directory
   - Use environment-specific settings in configuration files

3. **Utils**:
   - Store utility functions and classes in the `app/utils` directory
   - Each utility should have a single responsibility

4. **Pages**:
   - Store page components in the `app/pages` directory
   - Each page should be self-contained

5. **Models**:
   - Store data models in the `app/models` directory
   - Each model should represent a specific database entity

6. **Tests**:
   - Store tests in a `tests` directory
   - Mirror the structure of the `app` directory within the `tests` directory

## Best Practices

1. **Error Handling**:
   - Use specific exception types
   - Log exceptions with appropriate severity levels
   - Provide meaningful error messages

2. **Logging**:
   - Use the logging module for all logging
   - Use appropriate logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Include relevant context in log messages

3. **Comments**:
   - Use comments sparingly
   - Focus on explaining "why" rather than "what"
   - Keep comments up-to-date with code changes

4. **Testing**:
   - Write unit tests for all functionality
   - Aim for high test coverage
   - Use meaningful test names that describe the behavior being tested

5. **Dependencies**:
   - Minimize external dependencies
   - Keep dependencies up-to-date
   - Document dependencies in requirements.txt