# iROILS Evaluations

## Overview

The iROILS Evaluations repository is designed to facilitate the evaluation and management of entries related to institutional performance in various healthcare settings. This application leverages Streamlit for a user-friendly interface, allowing administrators and evaluators to manage data, conduct evaluations, and generate reports.

## Features

- **Admin Dashboard**: Admins can log in to manage institutional data, reset entries, and upload new data files.
- **Evaluator Dashboard**: Evaluators can log in to view assigned entries, submit evaluations, and track their progress.
- **Data Management**: Upload and manage entries in a PostgreSQL database, with support for Redis caching.
- **Evaluation Metrics**: Calculate and display evaluation metrics for institutions and individual evaluators.
- **User Authentication**: Secure login for both admins and evaluators with session management.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ara-Alexandrian/iROILS-Evaluations.git
   cd iROILS-Evaluations
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   conda create -n iroils python=3.8
   conda activate iroils
   pip install -r requirements.txt
   ```
3. Configure the PostgreSQL database and Redis settings in `app/config/config.ini`.
4. Run the Streamlit applications:
   ```bash
   python app/run_streamlit_apps.py
   ```

## Usage

- Access the admin dashboard at `http://localhost:8501`.
- Access the evaluator dashboard at `http://localhost:8502`.
- Use the PostgreSQL dashboard at `http://localhost:8503`.

## Configuration

The application uses a configuration file located at `app/config/config.ini`. Ensure to update the database connection details and API endpoints as necessary.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.
