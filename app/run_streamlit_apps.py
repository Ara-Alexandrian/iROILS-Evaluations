import subprocess
import os

# Activate the Conda environment and run the Streamlit apps
def main():
    # Path to your Conda environment's activation script
    conda_activate = "/config/miniconda3/etc/profile.d/conda.sh"
    conda_env_name = "iroils"
    
    # Activate Conda environment
    subprocess.run(f"source {conda_activate} && conda activate {conda_env_name}", shell=True, executable='/bin/bash')
    
    # Define the Streamlit apps and their ports
    apps = [
        ("app/admin_page.py", 8501),
        ("app/user_submission_page.py", 8502),
        ("app/postgres_dashboard_page.py", 8503)
    ]
    
    processes = []
    
    # Run each app in its own subprocess
    for app_path, port in apps:
        process = subprocess.Popen(
            ["streamlit", "run", app_path, f"--server.port={port}"], 
            shell=False
        )
        processes.append(process)
    
    # Wait for all processes to finish
    for process in processes:
        process.wait()

if __name__ == "__main__":
    main()
