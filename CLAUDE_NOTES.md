# Claude's Development Notes for iROILS-Evaluations

This document contains notes, observations, and development history of the iROILS-Evaluations project as analyzed by Claude. It serves as a diary to help maintain continuity when working on the codebase.

## System Architecture

The application is structured as a multi-dashboard Streamlit application with:

1. **Core Components**:
   - PostgreSQL database for persistent storage
   - Authentication system with role-based access control
   - Module-based architecture following service pattern

2. **Main Interfaces**:
   - Admin Dashboard for management operations
   - User Submission interface for evaluators
   - Analysis views with data visualization
   - Tag Analysis dashboard for specialized tag metrics

3. **Session Management**:
   - Dual session state systems (both custom SessionState and Streamlit's st.session_state)
   - Authentication persistance between pages
   - Role-based page restrictions

## Recent Changes (May 2025)

### Unified Dashboard Implementation

- Created a unified dashboard (`main_unified.py`) integrating all functionality through a single port (8501)
- Added sidebar navigation with role-appropriate options
- Implemented custom CSS to hide default Streamlit navigation elements
- Added "Return to Menu" buttons on all pages

### Authentication and Session Fixes

- Fixed session state sync issues between two parallel session systems
- Enhanced role management for admin and evaluator users
- Added better error messages for access restrictions
- Resolved login issues with the evaluator credentials

### UI Improvements

- Fixed Arrow conversion errors by implementing custom table displays
- Created specialized tag analysis dashboard with correlation metrics
- Added summary statistics and visualizations
- Fixed duplicate element ID errors with unique identifiers
- Improved institution selection and navigation

### Data Handling

- Added robust type handling for all data tables
- Improved handling of None/NaN values in dataframes
- Enhanced slider input validation for evaluations
- Added better error feedback for problematic data inputs

## Known Issues and Workarounds

1. **Arrow Type Conversion Errors**:
   - Occurs when attempting to display certain dataframes in Streamlit
   - Current solution: Convert all data to strings before display and use custom table renderers
   - Needs further monitoring for edge cases

2. **Session Synchronization**:
   - Two parallel session state systems (SessionState and st.session_state)
   - Current solution: Update both systems during login/logout
   - Consider consolidating to single system in future

3. **Navigation Between Pages**:
   - Some pages may have navigation issues
   - Current solution: Added "Return to Menu" buttons
   - Consider implementing more global state management

## Future Work Recommendations

1. **Backend Improvements**:
   - Consolidate session state handling to use only st.session_state
   - Add more robust error handling for database operations
   - Add database migration system for schema changes

2. **UI Improvements**:
   - Create more responsive layouts for mobile devices
   - Add more visualization options for tag analysis
   - Implement better feedback for long-running operations

3. **Feature Additions**:
   - Add user management interface for administrators
   - Implement audit logging for sensitive operations
   - Add export functionality for reports
   - Add comparison view for institutions

## Database Schema Reference

Key tables in the PostgreSQL database:

```
entries:
- id (SERIAL PRIMARY KEY)
- institution (VARCHAR)
- event_number (VARCHAR)
- data (JSONB)

evaluations:
- id (SERIAL PRIMARY KEY)
- institution (VARCHAR)
- evaluator (VARCHAR)
- entry_number (VARCHAR)
- summary_score (INTEGER)
- tag_score (INTEGER)
- feedback (TEXT)

institution_stats:
- institution (VARCHAR PRIMARY KEY)
- cumulative_summary (FLOAT)
- cumulative_tag (FLOAT)
- total_evaluations (INTEGER)
```

## Authentication Reference

Admin credentials:
- Username: `iroils` / Password: `iROILS`
- Username: `1` / Password: `1` (for testing)

Evaluator credentials (examples):
- UAB: Username: `aalexandrian` / Password: `S9hL3dT7`
- MBPCC: Username: `astam` / Password: `A3nR6yP7`