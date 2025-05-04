    # mb_run_streamlit_apps.py

import subprocess
import os
import socket

def get_local_ip():
  """Get the local IP address of the machine."""
  try:
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(('8.8.8.8', 1))  # Connecting to Google DNS to get local IP
      local_ip = s.getsockname()[0]
      return local_ip
  except Exception as e:
      print(f"Error getting local IP: {e}")
      return None
  finally:
      s.close()

def main():
  # Get local IP
  local_ip = get_local_ip()
  
  # Path to your Conda environment
  conda_activate = "/config/miniconda3/etc/profile.d/conda.sh"  # Update this path
  conda_env_name = "iroils"  # Your conda environment name
  
  # Activate Conda environment
  subprocess.run(f"source {conda_activate} && conda activate {conda_env_name}", 
                shell=True, 
                executable='/bin/bash')
  
  # Define the Streamlit apps and their ports
  apps = [
      {
          "path": "iROILS-Evaluations/app/admin_page.py",
          "port": 8501,
          "address": local_ip
      },
      {
          "path": "iROILS-Evaluations/app/user_submission_page.py",
          "port": 8502,
          "address": local_ip
      },
      {
          "path": "iROILS-Evaluations/app/postgres_dashboard_page.py",
          "port": 8503,
          "address": local_ip
      }
  ]
  
  processes = []
  
  # Run each app in its own subprocess
  for app in apps:
      cmd = [
          "streamlit", 
          "run", 
          app["path"],
          "--server.port", str(app["port"]),
          "--server.address", app["address"]
      ]
      
      process = subprocess.Popen(
          cmd,
          shell=False
      )
      processes.append(process)
      print(f"Started app at http://{app['address']}:{app['port']}")
  
  try:
      # Wait for all processes to finish
      for process in processes:
          process.wait()
  except KeyboardInterrupt:
      print("\nShutting down all Streamlit apps...")
      for process in processes:
          process.terminate()

if __name__ == "__main__":
  main()