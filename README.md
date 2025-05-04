# iROILS Evaluations

Radiation Oncology Incident Learning System (ROILS) Evaluations is an application for healthcare institutions to track and evaluate radiation therapy incidents.

## Overview

The iROILS Evaluations application provides a web-based platform for multiple institutions to:

1. Upload radiation therapy incidents for evaluation
2. Assign evaluators to review incidents
3. Collect standardized feedback and scoring
4. Analyze evaluation results across institutions and tags

The application supports two types of users:
- **Administrators**: Can manage institutions, upload data, and view analytics
- **Evaluators**: Can review and score assigned incidents

## Key Features

- **Unified Dashboard**: Single-port access to all features through an intuitive navigation menu
- **Admin Dashboard**: Manage institutional data, reset entries, and upload new data files
- **User Submission**: Submit evaluations with summary and tag scores plus textual feedback
- **Data Analysis**: Interactive visualizations and comparative statistics
- **Tag Analysis**: Specialized dashboard for tag-based analysis and patterns
- **User Authentication**: Secure role-based access control with session management

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL database
- Git

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/iROILS-Evaluations.git
   cd iROILS-Evaluations
   ```

2. Create a virtual environment (two options):

   **Option A: Using Conda with environment.yml** (recommended):
   ```bash
   conda env create -f environment.yml
   conda activate iroils
   ```

   **Option B: Manual setup with conda**:
   ```bash
   conda create -n iroils python=3.8
   conda activate iroils
   pip install -r requirements.txt
   ```

   **Option C: Using venv**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Configure the application:
   - Edit `app/config/config.ini` to set your database credentials and other settings
   - By default, the application will create the necessary database tables on startup

## Usage

### Starting the Application

Run the unified application:

```
python app/run_streamlit_unified.py
```

This will start a Streamlit server on port 8501 with access to all features through a unified interface.

For backward compatibility, you can also run the separate dashboards:
```
python app/run_streamlit_apps.py
```

This will start three Streamlit servers:
1. **Admin Dashboard** (port 8501): For administrative tasks
2. **Evaluator Dashboard** (port 8502): For evaluators to submit evaluations
3. **Database Dashboard** (port 8503): For monitoring database activity

### Authentication

- **Admin Login**: Use the admin credentials set in the configuration
  - Default: Username: `admin`, Password: `!admin`
  - For testing: Username: `1`, Password: `1`
  
- **Evaluator Login**: Use the evaluator-specific credentials
  - Example UAB evaluator: Username: `aalexandrian`, Password: `S9hL3dT7`
  - Example MBPCC evaluator: Username: `astam`, Password: `A3nR6yP7`

### Administrative Tasks

As an administrator, you can:

1. Upload incident data in Excel format
2. Select incidents for evaluation
3. View evaluation statistics and tag analysis
4. Reset institution data

### Evaluation Tasks

As an evaluator, you can:

1. View assigned incidents
2. Submit evaluations with summary and tag scores
3. Provide textual feedback
4. Track your evaluation progress

## Development

### Project Structure

The project follows a modular architecture:

```
iROILS-Evaluations/
├── app/                        # Main application directory
│   ├── config/                 # Configuration management
│   ├── core/                   # Core application functionality
│   ├── exceptions/             # Custom exception classes
│   ├── models/                 # Data models
│   ├── pages/                  # UI page components
│   ├── services/               # Service layer
│   ├── static/                 # Static assets
│   └── utils/                  # Utility functions
├── data/                       # Data storage directory
├── resources/                  # Project resources
└── tests/                      # Test suite
```

See [STRUCTURE.md](STRUCTURE.md) for a detailed description of the project structure.

### Coding Standards

This project follows a consistent coding style. See [STYLE_GUIDE.md](STYLE_GUIDE.md) for detailed guidelines.

### Testing

Run the test suite:

```
pytest
```

## Development Notes

### Recent Improvements

- **Unified Interface**: Consolidated multiple dashboards into a single-port application with navigation
- **Enhanced Tag Analysis**: Added comprehensive tag analysis dashboard with visualizations
- **UI Improvements**: Improved tables with proper string handling to prevent Arrow conversion errors
- **Session Management**: Fixed authentication and session state management
- **Navigation**: Added return-to-menu buttons and better access controls

### Known Issues

- Some data preview and form submissions may trigger Arrow conversion errors if data types are inconsistent
- Session timeout may not always be detected correctly across pages

### Future Work

- Improve data import error handling
- Add user management interface for administrators
- Enhance visualization capabilities for tag analysis
- Implement comprehensive validation of imported data

## License

This project is proprietary and intended for use by authorized institutions only.

## Acknowledgements

- Mary Bird Perkins Cancer Center (MBPCC)
- University of Alabama at Birmingham (UAB)