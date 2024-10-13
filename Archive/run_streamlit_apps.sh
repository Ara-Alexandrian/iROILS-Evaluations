#!/bin/bash

# Activate the Conda environment
source /config/miniconda3/etc/profile.d/conda.sh
conda activate iroils

# Run the main Streamlit apps
streamlit run /config/github/iROILS-Evaluations/app.py --server.port 8501 &
streamlit run /config/github/iROILS-Evaluations/user_submission.py --server.port 8502 &
streamlit run /config/github/iROILS-Evaluations/postgres_dashboard.py --server.port 8503 &

# Wait for all processes to complete
wait
