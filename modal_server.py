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
        .run_commands(
         "apt-get update",
        "apt-get install -y build-essential python3 python3-pip git cmake libeigen3-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev libsuitesparse-dev pkg-config libhdf5-dev gcc libgl1-mesa-glx libglib2.0-0",
        "apt-get remove -y libeigen3-dev",  # Remove the existing version of Eigen3
    )
    .run_commands(
        "apt-get install -y  cmake libsuitesparse-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev"
    )
   .run_commands(
       "apt-get install -y libceres-dev"
   )
   .run_commands(
       "git clone https://gitlab.com/libeigen/eigen.git eigen"
   )
   .workdir("/eigen")
   .run_commands(
       "git checkout 3.4",
        "mkdir build",
   )
   .workdir("/eigen/build")
   .run_commands(
        "cmake ..",
        "make",
        "make install",
   )
   .workdir("/")
   .run_commands("ls")
    .run_commands(
        "git clone https://github.com/cvg/implicit_dist.git implicit_dist",
        )
    .workdir("/implicit_dist")
    .run_commands(
        "ls",
        "python3 -m venv .venv",
        ". .venv/bin/activate",
        "pip install .",
        "pip freeze",
    )
    .workdir('/root')
    .run_commands("ls")
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