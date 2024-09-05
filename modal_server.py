import subprocess
from pathlib import Path

import modal


image  = (
    modal.Image.debian_slim(python_version="3.8")
    .run_commands(
        "apt-get update",
        "apt-get install -y pkg-config libhdf5-dev gcc libgl1-mesa-glx libglib2.0-0",
        "pip install --upgrade pip",
    )
    .pip_install_from_requirements("src/requirements.txt")
    .pip_install("kornia")
    .pip_install('pytorch_lightning')
)

app = modal.App(name="unav-streamlit", image=image)

project_dir_local_path = Path(__file__).parent / "src"
print('project_dir_local_path:', project_dir_local_path)
project_dir_remote_path = Path("/root/src")

if not project_dir_local_path.exists():
    raise RuntimeError(
        "Project directory not found! Ensure the 'src' directory is in the correct path."
    )

project_mount = modal.Mount.from_local_dir(
  local_path=project_dir_local_path,remote_path=project_dir_remote_path
)

# ## Spawning the Flask server with CMD
#
# Inside the container, we set the FLASK_APP environment variable and run the server using CMD.

@app.function(
    allow_concurrent_inputs=100,
    mounts=[project_mount],
    image = image,
)
@modal.web_server(port=5001,startup_timeout=60)
def run():

    # Command to run the Flask server
    server_cmd = ["python", "src/server.py"]
    
    try:

        
        # Run the Flask server
        subprocess.run(server_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        raise