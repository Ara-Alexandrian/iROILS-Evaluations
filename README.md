# iROILS Evaluations

Radiation Oncology Incident Learning System (ROILS) Evaluations is an application for healthcare institutions to track and evaluate radiation therapy incidents.

## Overview

The iROILS Evaluations application provides a web-based platform for multiple institutions to:

1. Upload radiation therapy incidents for evaluation
2. Assign evaluators to review incidents
3. Collect standardized feedback and scoring
4. Analyze evaluation results across institutions

The application supports two types of users:
- **Administrators**: Can manage institutions, upload data, and view analytics
- **Evaluators**: Can review and score assigned incidents

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

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure the application:
   - Edit `app/config.ini` to set your database credentials and other settings
   - By default, the application will create the necessary database tables on startup

## Usage

### Starting the Application

Run the application launcher:

```
python run.py
```

This will start three Streamlit servers:

1. **Admin Dashboard** (port 8501): For administrative tasks
2. **Evaluator Dashboard** (port 8502): For evaluators to submit evaluations
3. **Database Dashboard** (port 8503): For monitoring database activity

### Authentication

- **Admin Login**: Use the admin credentials set in the configuration
  - Default: Username: `iroils`, Password: `iROILS`
  
- **Evaluator Login**: Use the evaluator-specific credentials
  - Default evaluators are configured for UAB and MBPCC institutions

### Administrative Tasks

As an administrator, you can:

1. Upload incident data in Excel format
2. Select incidents for evaluation
3. View evaluation statistics
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

## License

This project is proprietary and intended for use by authorized institutions only.

## Acknowledgements

- Mary Bird Perkins Cancer Center (MBPCC)
- University of Alabama at Birmingham (UAB)