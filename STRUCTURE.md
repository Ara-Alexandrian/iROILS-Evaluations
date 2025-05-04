# iROILS Evaluations Project Structure

This document outlines the improved structure of the iROILS Evaluations project.

## Directory Structure

```
iROILS-Evaluations/
├── app/                        # Main application directory
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # Application entry point
│   ├── config/                 # Configuration management
│   │   ├── __init__.py
│   │   ├── config.ini          # Configuration settings
│   │   └── config_manager.py   # Configuration loading and access
│   ├── core/                   # Core application functionality
│   │   ├── __init__.py
│   │   ├── app_state.py        # Application state management
│   │   └── session.py          # Session management
│   ├── exceptions/             # Custom exception classes
│   │   ├── __init__.py
│   │   ├── auth_exceptions.py  # Authentication exceptions
│   │   ├── data_exceptions.py  # Data handling exceptions
│   │   └── network_exceptions.py # Network-related exceptions
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── entry.py            # Entry data model
│   │   ├── evaluation.py       # Evaluation data model
│   │   └── institution.py      # Institution data model
│   ├── pages/                  # UI page components
│   │   ├── __init__.py
│   │   ├── admin_page.py       # Admin dashboard
│   │   ├── analysis_page.py    # Analysis dashboard
│   │   ├── dashboard_page.py   # Postgres dashboard
│   │   ├── overview_page.py    # Overview dashboard
│   │   ├── selection_page.py   # Selection page
│   │   └── submission_page.py  # User submission page
│   ├── services/               # Service layer
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Authentication service
│   │   ├── database_service.py # Database access service
│   │   ├── evaluation_service.py # Evaluation processing service
│   │   └── institution_service.py # Institution management service
│   ├── static/                 # Static assets
│   │   ├── css/                # CSS stylesheets
│   │   ├── images/             # Images and logos
│   │   └── js/                 # JavaScript files
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── analysis_utils.py   # Analysis helper functions
│       ├── data_utils.py       # Data manipulation utilities
│       └── network_utils.py    # Network-related utilities
├── data/                       # Data storage directory
├── resources/                  # Project resources
│   ├── MBPCC.png               # MBPCC logo
│   ├── UAB.png                 # UAB logo
│   ├── authors                 # Author information
│   ├── styles.css              # Streamlit CSS customizations
│   └── usernames               # User credential information
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Test configuration
│   ├── integration/            # Integration tests
│   └── unit/                   # Unit tests
├── .gitignore                  # Git ignore file
├── README.md                   # Project documentation
├── requirements.txt            # Project dependencies
├── STRUCTURE.md                # This file
└── STYLE_GUIDE.md              # Coding style guide
```

## Component Relationships

1. **Service Layer Pattern**:
   - Services encapsulate business logic and data access
   - Pages interact with services, not directly with data storage
   - Services are responsible for coordinating between models and data persistence

2. **Model-View Separation**:
   - Models (`app/models/`) define data structures
   - Views (`app/pages/`) present data to users
   - Services (`app/services/`) handle business logic

3. **Configuration Management**:
   - Centralized configuration via `ConfigManager`
   - Environment-aware settings (home/work)
   - Single responsibility for configuration access

4. **Utility Organization**:
   - Grouped by functionality domain
   - Focused on reusable helper functions
   - Clear separation from business logic

## Benefits of New Structure

1. **Improved Maintainability**:
   - Clear separation of concerns
   - Single responsibility principle applied
   - Isolation of dependencies

2. **Better Testability**:
   - Decoupled components for easier testing
   - Clear interfaces between components
   - Dedicated test structure

3. **Enhanced Scalability**:
   - Modular design for adding new features
   - Consistent patterns for extensibility
   - Reduced coupling between components

4. **Clearer Documentation**:
   - Self-documenting structure
   - Explicit component relationships
   - Standardized organization